# Interactive Clustering and Analysis Tool for GPS data

This tool was created as part of my MSc Thesis project in 2023 in which I designed and used an interactive clustering method to analyze oystercatcher data. It is tailed to my specific methods, data and needs during this project but it could certainly be useful for others too. I have tried to make it as flexible and robust as I reasonably could when developing it, but ultimately it was not possible to extensively test everything beyond my own project. I cannot guarantee that the code is 100% free of errors, bugs, mistakes or any other unintentional issues that may sneak in. As such, I'm not responsible for any issues that can result from the use of this tool.

You may use this tool for personal use or research purposes as well as make modifications and improvements on top of the existing tool, such as improving the clustering method or adding other analysis methods. Please do give me credit for the (original) tool. Do not sell the code provided here. See license.txt for the specific license.

I do not plan to continue working on the tool and am leaving it here so it may be used by others who find it useful, either in its current state or by adding to it.
In case of issues regarding the use of the tool specifically (NOT general 'how to' Python questions), such as errors when using the tool as intended, you can email me at marije349@outlook.com and I will try to help if you clearly describe the issue.
However, I will NOT respond to requests to add a feature to the tool, to make it work differently or any other modifications to the tool - it's not that I don't want to, I simply don't have the time to keep working on this tool.

## INSTALLATION INSTRUCTIONS
1. Create a virtual environment (not required but recommended)
2. Install the packages listed in requirements.txt
3. In the virtual environment, run run.py to start the tool

## HOW TO USE THE TOOL
1. **Preprocessing/preparation**
Before a data set can be clustered, it needs to be 'added' to the tool, which will save a few variables in the database which makes it considerably easier to plot the data each time.
There are two options:
	1. The first option incluces some preprocessing steps. This will require the minimum and maximum lat/long coordinates (in decimals) that define the geographic area that contains the data, which is what will be plotted each time. The tool will exclude any data outside of this area and save the resulting .csv file for future use in the tool. In addition, a daytime column (True/False) is added. If multiple years in the data, they will be separated.
	2. The second option assumes that your data is already confined to the 'area' described above, and skips the preprocessing steps. Instead, provide the animal id, year and the four coordinates which will simply be saved to the database so they can be used.

It is NOT possible to use the tool if you skip this part.

2. **Clustering**
Start the interactive clustering process for the provided individual, the tool explains what's happening. Saved clusters are saved to the database so they can be used for analysis.

3. **Analysis**
A few different options to analyse a clustered dataset.

4. **Editing existing clusterings**
A saved clustering can be edited in a few ways.
	1. Change clustering name (the name that describes the clustering)
	2. Change a cluster's name 
	3. Continue interactive clustering from this data
