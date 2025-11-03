TECHNICAL UNIVERSITY OF DENMARK MSc Civil Engineering / 41934 Advanced Building Information Modeling (BIM) / 2025 Autumn Semester / Assignment 2 - Use Case / Lecturer: Associate Professor Tim Pat McGinley / Students: Ida Sofie Fiksdal s253450 & Elisa Steen-Hansen s253443    

# Assignment 3: Tool

**Note:**
In Assignment 2, the task specified that loads from slabs and beams should be used as input to the script in order to verify the columns’ capacity and utilization. However, due to the other group having technical complications in transferring these loads from the BIM model, we decided instead to use point loads obtained from the Advanced Building Design report for Building 16 to complete and validate this tool.
We came to a conclusion, that our tool is still useful without loads from the model. As this tool takes a load as input and checks if the utilization is overridden.

## About the Tool:

**Q: State the problem / claim that your tool is solving, and state where you found that problem.**

A: As stated on page 11 of the report, the capacity is deemed sufficient. Accordingly, this tool will focus on verifying whether the axial capacity for the columns in the basement is adequate to resist the point loads from the report.

**Q: Description of the tool**

A: 
The script starts by importing structural data from the BIM model, and adjusts the model information to include necessary load and geometry data.
Next, it extracts the geometry and material properties of the columns and uses this information to calculate each column’s axial load capacity.
To determine if the columns are posisioned in the basement, the top height of each columns is extracted. Only columns with a top height in z= 0, 
with a tolerance of 2mm, is included in the calculations.
The computed capacities are then compared with the applied loads to evaluate whether the columns can safely carry their design loads stated in the report.
If a column’s capacity is insufficient, it is flagged for review; otherwise, it is marked as OK.
Finally, the results are compiled into a capacity control report, providing a summary of which columns pass or fail the capacity check.
 
**Q: 🚀Instructions to run the tool**

1. Requirements
- Python
- IfcOpenShell

2. Prepeare your IFC Model
- Save a structural model as an IFC file. 
- Place the file in the same folder as the script. 

3. Run the script
- Open the IFC model under "model"
- Apply the loads
- Run the code

4. Create a report with the results
- Run the last code in the script

The report with results from the calculations will appear in a txt.file called "Capacity.control.report.txt" in your files. 
Here you can check the column ID, geometry, loads, utilizations and if the columns are OK or insufficient. Here, the worst utilization
will be listed in the bottom of the report.

## Advanced Building Design

**Q: What Advanced Building Design Stage (A,B,C or D) would your tool be useful?**
A: Out tool would be most useful in stage B, for Advanced Building Design, while developing different building system options. But also at stage C when integrating the selected options with the client requirements.

**Q: Which subjects might use it?**
A: The tool is mainly for structural designer. 

**Q: What information is required in the model for your tool to work?**
A: Information such as material, geometry and dimensions for the different floors is required in the model for this tool to work. This is why IfcOpenShell is required. 








