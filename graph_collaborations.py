#!/usr/bin/env python

import argparse
import csv
import sys
import collections

"""Builds social network graphs based on author publications. The resulting files 
can be imported into Gephi which can, in turn, produce nice looking plots. """

skipped_authorships = set()
author_names = {}       # spelling -> faculty where spelling is how the author's name may appear in publication
class Faculty(object):
    """Object representing an author."""
    other_cols = []
    def __init__(self, membername, line):
        self.name = membername
        namefrags = self.name.split(",")
        if len(namefrags) == 3:
            self.lastname, self.other, self.firstname = self.name.split(",")
        else:
            self.lastname, self.firstname = self.name.split(",")
        self.firstname = self.firstname.strip()
        self.authorship = set()            # Spellings used for authorship
        self.publications = []
        self.trainees = []
        self.affiliations = []
        self.appointment = "Unknown"
        self.collaborations = 0
        self.othercols = {}
        
        for col in Faculty.other_cols:
            self.othercols[col] = line[col]
        
        initials = []
        initagg = ""
        for name in self.firstname.strip(".").split():
            initial = name[0]
            initials.append(initial)
            initagg += initial
            self.authorship.add("%s %s" % (self.lastname, initagg))

    def GetAuthorship(self):
        """We will use the first authorship spelling as the primary"""
        authorships = list(self.authorship)
        if len(authorships) > 0:
            return list(self.authorship)[0]
        return "%s %s" % (self.lastname, self.firstname[0])
    
    def other(self):
        """Generate an ordered list of the additional columns requested"""
        other = []
        print ""
        print "Other Col Headers: ", Faculty.other_cols
        print self.othercols
        for col in Faculty.other_cols:
            other.append(self.othercols[col])
        return other

    @classmethod
    def header(cls):
        header = "Id\tLabel\tWeight\tAppointment"
        if len(cls.other_cols) > 0:
            header = "%s\t%s" % (header, "\t".join(Faculty.other_cols))
        return header

    def __repr__(self):
         return "\t".join([self.GetAuthorship(), self.name, str(self.collaborations), self.appointment] + self.other())


def LoadAppointments(file, nodes, hdr_name, hdr_dep):
    """Build out the node list"""
    global author_names
    appointments = {}
    
    for line in csv.DictReader(file):
        faculty_name = line[hdr_name]
        appointments[faculty_name] = line[hdr_dep]
        faculty = Faculty(faculty_name, line)
        nodes[faculty_name] = faculty
        faculty.appointment = line[hdr_dep]
        
        # Grab specialized columns
        for col in Faculty.other_cols:
            faculty.othercols[col] = line[col]
        
        # Build up potential spellings in the publication line
        for name in faculty.authorship:
            if name not in author_names:
                author_names[name] = faculty
            else:
                print >> sys.stderr, "Overlapping Author Name %s: %s - %s" % (
                    name, author_names[name].name, faculty_name
                )
    return appointments
        
    

class Publication(object):
    def __init__(self, title, authors):
        """Austin AF, Compton LA, Love JD, Brown CB, Barnett JV. Primary and immortalized mouse epicardial cells undergo differentiation in response to TGFbeta. Dev Dyn. 2008 Feb;237(2):366-76. PubMed PMID: 18213583. No PMCID - Published before April 7, 2008."""

        global author_names 
        self.authors = []
        self.title = title
       
        for author in [x.strip() for x in authors.split(",")]:
            if author in author_names:
                self.authors.append(author_names[author])
        self.authors = list(set(self.authors))
                        
    @classmethod
    def header(cls):
        return "Target\tSource\tEdge_Title"

    def determineWeights(self, file):
        """Count the total number of active collaborations observed between the population"""
        authorlist = []
        if len(self.authors) > 1:
            for i in range(0, len(self.authors)):
                self.authors[i].collaborations+=1
                authorlist.append(self.authors[i].name)
        else:
            print >> sys.stderr, "^^ Too few authors: ", self.title, self.authors
        print >> file, self.title, "\t".join(authorlist)

    def appendEdges(self, edgelist):
        """Append the edges (pairs of collaborators) to the list. We'll sort 
          authors in case there are multiple lines with the same publication
          (this should avoid truly duplicated edges, but permit the same author
          pairs to collaborate multiple times and be counted as such)"""
        if len(self.authors) > 1:
            for i in range(0, len(self.authors)):
                members = [self.authors[i], None]
                for j in range(i + 1, len(self.authors)):
                    members[1] = self.authors[j]
                
                    if members[0].GetAuthorship() > members[1].GetAuthorship():
                        members = [members[1], members[0]]
                    edgelist.append("\t".join([
                           members[0].GetAuthorship(), 
                           members[1].GetAuthorship(), 
                           self.title
                    ]))
                     

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--node-source", type=argparse.FileType('r'), required=True, help="Filename associated with the node definitions")
parser.add_argument("-p", "--pub-source", type=argparse.FileType('r'), required=False, help="Filename associated with the edges. If left undefined, --node-source will be used")
parser.add_argument("-f", "--faculty-col", default="Faculty Name", help="Column name used for Faculty names")
parser.add_argument("-d", "--department-col", default="Primary Department", help="Column name used for Faculty members' primary department.")
parser.add_argument("-u", "--publication-col", default="Publication", help="Column name used for publications")
parser.add_argument("-c", "--other-cols", default="", help="Other columns to be kept from the node input (comma separated list)")
parser.add_argument("-o", "--output-name", required=True, help="Prefix used for all output and logs")
args = parser.parse_args()

othercols = []
if args.other_cols:
    othercols=args.other_cols.split(",")
    Faculty.other_cols = othercols

faculty = {}
publications = {}
edges = collections.defaultdict(list)
appointments = LoadAppointments(args.node_source, faculty, args.faculty_col, args.department_col)

# Permit the user to use the same file for both node details and publications
file = args.pub_source
if file is None:
    file = open(args.nodesource.name)
reader = csv.DictReader(file)

for line in reader:
    #Iterate over each author in the publication's author list. 
    #We assume that the author lists are terminated by a "." and the title
    #immediately follows (and again, followed by a dot)
    # If this is not true, the file needs to be corrected
    if line["Publication"].strip() != "No publications. Withdrew from MSTP.":
        parts = line[args.publication_col].split(".")
        if len(parts) >= 3:
            authors, title, remaining = parts[0:3]
    
            if title not in publications:
                pub = Publication(title, authors)
                publications[title] = pub
            else:
                print >> sys.stderr, "Redundant paper?", title
        elif parts != ["No publications / In progress"]:
            print "Skipping: ", parts

# Log the list of all issues related to publication authorship
with open("%s-publications.txt" % (args.output_name), "w") as file:
    for pub in publications:
        publications[pub].determineWeights(file)
    
# Generate the nodes file
with open("%s_nodes.tsv" % (args.output_name), "w") as file:
    print >> file, Faculty.header()
    for member in faculty:
        node = faculty[member]
        if node.collaborations > 0:
            print >> file, node
        else:
            print >> sys.stderr, "Skipping %s because they have no collaborations: " % (node.name)

# Generate the edges    
with open("%s_edges.tsv" % (args.output_name), "w") as file:
    print >> file, Publication.header()
    edges = []
    for pub in publications:
        publications[pub].appendEdges(edges)
    print >> file, "\n".join(edges)


