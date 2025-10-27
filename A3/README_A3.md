# Assignment 3: Tool

## About the Tool:

**Q: State the problem / claim that your tool is solving, and state where you found that problem.**

A: As stated on page 11 of the report, the capacity is deemed sufficient. Accordingly, this tool will focus on verifying whether the axial capacity for the columns in the basement is adequate to resist the loads imposed by the beams and slabs from the floors above.

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
- Save the structural model "25-16-D-STR" as an IFC file. 
- Place the file in the same folder as the script. 

3. Run the script
- Open the IFC model under "model"
- Apply the loads
- Run the code

4. Save the Outputs to a file
- Save the printed outputs to a text file by:

python A3.py > results.text





