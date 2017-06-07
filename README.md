# Wiki-Calendar
## Setup
### Setting People
Enter the list of desired names and roles separated by a tab into the `people.config` file.

_Example:_
```
Person_0	Lead
Person_1	Software
Person_2	Hardware
```

### Setting Dates
Enter the start and end day, month, and year into the `wiki.config` file.

_Example:_
```
start_month=5
start_day=27
start_year=2017
end_month=7
end_day=12
end_year=2017
```

### Setting up Flask
Install the Flask module for Python. 

Next run the following command in the terminal: `export FLASK_APP=ROOTDIRECTORY/wiki/wiki.py`

_Replace ROOTDIRECTORY with the root directory of the project._

### Initializing the Database
You can manually initialize the database with `flask initdb` or let the program generate it on startup. Both will generate a file called wiki-YEAR.db with the names, roles, and dates entered in the config files. 

_YEAR will be replaced with the current year._

_Example:_ 

`wiki-17.db`

## Using the Website
### Turning on the website
To start the website run the following command in the terminal: `flask run`

### Styling Text
If you want to add style to input text, write the css for the text and then a `|` and then the text.

_Example:_
```
color:red; | Closed
```
_This would create a red `Closed`_

### Inputting Multiple Dates or Names
If you inspect the HTML for the page, you can delete the `readonly` tag from the input boxes for name and date. This will allow you to use the `*` character to affect all dates for a name or all names for a date.

_Example:_

```
Name:   Person_0
Date:   *
Entry:  N
```
_Will fill out an `N` for the entire week for Person_0_

_Example:_

```
Name:   *
Date:   6-7-17
Entry:  Closed
```
_Will set everyone to `Closed` on 6-7-17_
