# traceback-gui
Display your traceback in a tkinter window. And you can view variables in each frame through `tkinter.ttk.Treeview` widget.

--------

## Usage
```python
import traceback_gui
traceback_gui.set_hook()
# Your code here.
```

### Example: silly_add_1.py
Here is a example to show you how is traceback-gui.
#### Code:
```python
import io
import sys

import traceback_gui

traceback_gui.set_hook()

# This program looks very silly. But it can show you how is traceback-gui.


def get_input(prompt):
    return input(prompt)


def add_1_with_input():
    first = get_input('A number: ')
    return first + 1


sys.stdin = io.StringIO('99\n')
try:
    print('Add 1 program')
    result = add_1_with_input()
    print(result)
except TypeError:
    print('Oh, there is an error!', error=TypeError)

```
#### Result:
A window popped up:
![image](https://www.github.com/KevinLi-py/traceback-gui/raw/master/readme_resources/1.1.png)

Click the `+` button of the second treeview. You can see the value of variable `first` is a str. Then you can know why the exception happend:
![image](https://www.github.com/KevinLi-py/traceback-gui/raw/master/readme_resources/1.2.png)

Click another tab. You can see the exception occorred during handling the above exception.
![image](https://www.github.com/KevinLi-py/traceback-gui/raw/master/readme_resources/1.3.png)

