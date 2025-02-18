## There are three branches for this github repository:
1. Main
2. constantControl
3. tempConstant

## to use
1. Clone the repository using the following command: `git clone https://github.com/ellipsometry-hu/Control.git
2. Change into the repository directory: `cd Control`
3. fetch the all branches using : git fetch origin constantControl
                                  git fetch origin tempConstant
4. checkout the constantControl branch for continuous temperature drop very slowly using: `git checkout constantControl`  
4. checkout to the constantControl branch using: `git checkout constantControl
5. run main file using `python main.py `
6. to switch to the tempConstant branch for constant temperature at dew point : `git checkout tempConstant`
7. run main file using `python main.py `

## libraries required
Python >=3.11
1. pyserial
2. pyvisa
3. openpyxl
4. pypi
5. pandas
6. matplotlib
