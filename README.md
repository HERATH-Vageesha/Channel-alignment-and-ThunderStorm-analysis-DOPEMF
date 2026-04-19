# Channel-alignment-and-ThunderStorm-analysis-DOPEMF
STEPS for parshing through documentation

01) The first document to read through would be the "Channel Alignment protocol_descriptor based registration" and this file has two seperate attached samples associated with it for practice including

                    A. AVG_ATTO647N channel stacks (1)
                    B. AVG_Cy3b channel stacks (1)


02) The second document is labled as "ThunderStorm analysis protocol" and the specifics of how to use ThunderStorm along with the camera settings and found within the document. For practice the document 


                    A. AVG_ATTO647N channel stacks (1)

is used.

03) Once the .csv files are extracted using ThunderStorm analysis software, the sample is run through a custom code for quantifiying misalingment and generating quiver plots.
The INPUT files for the code include:


                    a) ATTO647N.csv

                    b) Cy3b.csv
For the code provided named "Image anlignment_quanitification code.py"

The input file names are available under

        # --------------------------------------------------------------------------------------
        # FILE NAMES
        # --------------------------------------------------------------------------------------
        CY3B_FILE = "Cy3b.csv"
        ATTO_FILE = "ATTO647N.csv"

