TECHNICAL UNIVERSITY OF DENMARK MSc Civil Engineering / 41934 Advanced Building Information Modeling (BIM) / 2025 Autumn Semester / Assignment 2 - Use Case / Lecturer: Associate Professor Tim Pat McGinley / Students: Ida Sofie Fiksdal s253450 & Elisa Sten-Hansen  

## A2a: About your group

**Q: How much do you agree with the following statement: I am confident coding in Python**

A: 0. This is the first time that both of us are coding in Python

Our group’s focus area is columns, and we work as analysts.

## A2b: Identify Claim

**Q: Select which building(s) to focus on for your focus area**

A: We'll be focusing at building #2516

**Q: Identify a ‘claim’ / issue / fact to check from one of those reports.**

A: As stated on page 11 of the report, the capacity is deemed sufficient, with a utilization of 27%. Accordingly, our assessment will focus on verifying whether the axial capacity is adequate to resist the loads imposed by the beams and slabs.

**Q: Justify your selection of your claim**
A: By focusing on this aspect within the BIM model, we ensure that the interaction between structural elements is properly accounted for and that potential risks of underestimation of load transfer are minimized.


## A2c: Use Case


**Q: How would you check this claim?**

A: 

1. Repeat for every floor:
   - 1.1 To check this claim, we have to repeat this action for every column on every floor:
     - 1.1.1 Check the length of the column.
     - 1.1.2 Check the area for concrete and reinforcement from a cross-section of the column.
     - 1.1.3 Check the design values and partial factors for concrete and steel
     - 1.1.4 (if it's not in the IFCModel, we will use the data from the report).
     - 1.1.5 Calculate the capacity of the columns.
   - 1.2 Apply loads from slabs and beams.
   - 1.3 Check if the results are okay.
2. Generate a report that shows the results.

**Q: When would this claim need to be checked?**

A: Verifying Ultimate Limit State (ULS): Axial capacity NRd against the design load effects from the slabs and beams NEd.

**Q: What information does this claim rely on?**

A: Mainly dimensions of the columns in the IFC-model, aswell as the loads from the other analysts codes.

**Q: What phase? planning, design, build or operation.**

A: During the design phase

**Q: What BIM purpose is required? Gather, generate, analyse, communicate or realise?**

A: Analyze

**Q: Review use case examples - do any of these help?, What BIM use case is this closest to? If you cannot find one from the examples, you can make a new one.**

A: 
- **08: Engineering Analysis** Ensures structural safety and compliance with codes
- **11: Phase Planning (4D Modelling)** Avoids design errors and costly rework
- **13: 3D Control and Planning** Improves planning accuracy and cost control
- **14: Construction Coordination** Reduces risk of defects and safety issues during erection
- **xx: Rehabilitation** Supports sustainable reusing of structures and avoids overdesign. (Created our own)

## A2g: Identify appropriate software licence

**Q: What software licence will you choose for your project?**

A: We will use Python as the main software for this project, asweel as Blender 4.5

# Workflow Chart

![Workflow Chart](Workflow%20chart.svg)


