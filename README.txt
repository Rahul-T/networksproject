Programming assignment 2: Milestone 3

Group members:
Rahul Tholakapalli (rtholakapalli3@gatech.edu)
Hrisheek Radhakrishnan (radhakrishnan.hrisheek@gatech.edu)




File submitted:
star-node.py (main file to be executed for each individual star node)
README.md (documentation about program/how to use)
tester.txt (sample file used to test file transfer between nodes)


To run type:
python3 ./star-node.py nodename localport pocaddress pocport maxnodes

Examples:

(With no poc)
python3 ./star-node.py abc 12102 0 0 3

(With poc)
python3 ./star-node.py def 12002 networklab3.cc.gatech.edu 12003 3

python3 ./star-node.py ghi 12003 networklab1.cc.gatech.edu 12102 3

Known limitations:
This program may not work as intended when ran for an extremely long time