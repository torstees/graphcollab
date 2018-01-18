# graphcollab
Simple social network graph generation to be used to plot academic associations 
through publications

## Dependencies 
* Python 2.7.x
* A Graph Visualization tool (for graphical plots)  I use https://gephi.org/

## The Basics
Generates 2 tab separated files: (name)_nodes.tsv and (name)_edges.tsv
    
These are formatted as ready for import into Gephi. The nodes file will contain
information useful for labeling, shading nodes and the edges file will contain
the actual network connections. 

Required parameters include: --node-source, --output-name which correspond to 
a comma separated file for input and the prefix used for output. Please see
program's built in help (--help) for more configuration options. 

## Authors
The author name should be spelled last name, followed by a "," followed by a 
space either the first name or initial. A middle name can follow the first with
a space in between. Middle initials must appear with a space following the 
first name (or initial). 

## Publications
Currently, publications are expected to be in the following format: 
[author list]. [title]. [anything else]

If there is anything following the title, it must end with a ".".

The author list should have multiple authors separated by a space. Each author
should be represented as their lastname, followed by a "," followed by one or
more initials. These indicators must be identifiable by inspection of the author's
name from the node file. 