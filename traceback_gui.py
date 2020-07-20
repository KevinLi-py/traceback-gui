import sys
import linecache
import textwrap
from types import TracebackType
import types
from tkinter import *
from tkinter.ttk import *


class ScrolledText(Text):
    def __init__(self, master=None, **kw):
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        self.vbar.pack(side=RIGHT, fill=Y)

        kw.update({'yscrollcommand': self.vbar.set})
        Text.__init__(self, self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        self.vbar['command'] = self.yview

        # Copy geometry methods of self.frame without overriding Text methods -- hack!
        text_meths = vars(Text).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


class ScrolledTreeview(Treeview):
    def __init__(self, master=None, **kw):
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        self.vbar.pack(side=RIGHT, fill=Y)

        kw.update({'yscrollcommand': self.vbar.set})
        super().__init__(self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        self.vbar['command'] = self.yview

        # Copy geometry methods of self.frame without overriding Treeview methods -- hack!
        treeview_meths = vars(Text).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(treeview_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


class VariableView(ScrolledTreeview):
    def __init__(self, master: ScrolledText):
        super().__init__(master, show='tree', columns=('type', 'value'))
        self.column('#0', stretch=FALSE, width=240)
        self.heading('type', text='type')
        self.column('type', stretch=FALSE, width=100)
        self.heading('value', text='value')
        self.column('value', stretch=TRUE, width=500)
        self.parent_index = master.index('end')
        master.window_create(self.parent_index, padx=4, pady=4, window=self)
        self.master_text = master

        self.group_iids = {}
        self.iid_values = {}
        self.bind('<<TreeviewOpen>>', self.treeview_open_event)

    def add_variable_group(self, name):
        self.group_iids[name] = self.insert('', 'end', text=name, open=False)

    def add_variable(self, group, name, value):
        iid = self.insert(self.group_iids[group], 'end', text=name, values=(_get_type(value), repr(value)))
        self.iid_values[iid] = value

    def treeview_open_event(self, event):
        selection = self.selection()
        if not selection:
            return
        try:
            # print(self.get_children(selection))
            selection = selection[0]
            if len(self.get_children(selection)) == 0:
                value = self.iid_values[selection]
                items = []

                if isinstance(value, dict) or (hasattr(value, '__getitem__')
                                               and hasattr(value, '__len__') and hasattr(value, 'items')):
                    items.extend((repr(k), v) for k, v in value.items())

                if isinstance(value, (tuple, list)) or (hasattr(value, '__getitem__')
                                                        and hasattr(value, '__len__')):
                    items.extend((repr(i), v) for i, v in enumerate(value))

                for key in dir(value):
                    if hasattr(value, key) and not key.startswith('__'):
                        items.append((key, getattr(value, key)))

                # print(items)
                for k, v in items:
                    iid = self.insert(selection, 'end', text=k, values=(_get_type(v), repr(v)))
                    self.iid_values[iid] = v

        except (LookupError, TypeError, ValueError):
            pass
            # import traceback
            # traceback.print_exc()


class Page(ScrolledText):
    FONT_FAMILY = 'consolas'
    FONT_SIZE = 10

    def __init__(self, master: Notebook, title):
        super().__init__(master, relief='flat', font=(self.FONT_FAMILY, self.FONT_SIZE), cursor='arrow')

        self.tag_configure('additional-message', foreground='#0000ff')
        self.tag_configure('filename', foreground='#00ff00')
        self.tag_configure('lineno', foreground='#008000', font=(self.FONT_FAMILY, self.FONT_SIZE, 'bold'))
        self.tag_configure('error-lineno', foreground='#ff0000', font=(self.FONT_FAMILY, self.FONT_SIZE, 'bold'))
        self.tag_configure('scope', foreground='#008080')
        self.tag_configure('code', background='#c0c0c0')
        self.tag_configure('error-type', foreground='#ff0000', font=(self.FONT_FAMILY, self.FONT_SIZE, 'bold'))
        self.tag_configure('error-message', foreground='#ff00ff')

        master.add(self, sticky='nsew', text=title)

    def write_text(self, text, tag=None):
        self.insert('end', text, tag)

    def write_code(self, filename, error_lineno):
        for lineno, code_line in _get_code(filename, error_lineno):
            self.write_text('{:7d} '.format(lineno), 'error-lineno' if lineno == error_lineno else 'lineno')
            self.write_text(code_line, 'code')
            self.write_text('\n')

    def write_vars(self, global_vars, local_vars):
        variable_view = VariableView(self)
        variable_view.add_variable_group('globals')
        variable_view.add_variable_group('locals')
        for key, value in global_vars.items():
            variable_view.add_variable('globals', key, value)
        for key, value in local_vars.items():
            variable_view.add_variable('locals', key, value)


class TracebackPlusWindow(Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title('Traceback GUI')
        self.notebook = Notebook(self)
        self.notebook.pack(fill='both', expand=True)

    def show_traceback(self, exception=None):
        if exception is None:
            exception = sys.exc_info()[1]

        additional_message = None
        if exception.__cause__ is not None:
            self.show_traceback(exception.__cause__)
            additional_message = ("The above exception ({}) was the direct cause "
                                  "of the following exception:".format(_get_type(exception.__cause__)))
        elif exception.__context__ is not None and not exception.__suppress_context__:
            self.show_traceback(exception.__context__)
            additional_message = ("During handling of the above exception ({}), "
                                  "another exception occurred:".format(_get_type(exception.__context__)))
        self._show_traceback(exception, additional_message)

    def _show_traceback(self, exception: BaseException, additional_message=None):
        page = Page(self.notebook, _get_type(exception))

        if additional_message is not None:
            page.write_text(additional_message, 'additional-message')
            page.write_text('\n\n')

        page.write_text('Traceback (most recent call last):\n')
        for tb in _iter_tb(exception.__traceback__):
            lineno = tb.tb_lineno
            filename = tb.tb_frame.f_code.co_filename
            scope = tb.tb_frame.f_code.co_name
            # page.write_text('  File "{}", line {}, in {}\n')
            page.write_text('  File "')
            page.write_text(filename, 'filename')
            page.write_text('", line ')
            page.write_text(str(lineno), 'lineno')
            page.write_text(', in ')
            page.write_text(scope, 'scope')
            page.write_text('\n')
            page.write_code(filename, lineno)
            page.write_text('  variables: \n', 'additional-message')
            page.write_vars(tb.tb_frame.f_globals, tb.tb_frame.f_locals)
            page.write_text('\n')

        page.write_text(_get_type(exception), 'error-type')
        page.write_text(': ')
        page.write_text(str(exception), 'error-message')
        page.write_text('\n')
        page['state'] = 'disabled'


def _iter_tb(tb: TracebackType):
    while tb is not None:
        yield tb
        tb = tb.tb_next


def _get_type(exception: BaseException):
    exc_type = type(exception)
    stype = exc_type.__qualname__
    smod = exc_type.__module__
    if smod not in ("__main__", "builtins"):
        stype = smod + '.' + stype
    return stype


def _get_code(filename, error_lineno):
    all_lines = linecache.getlines(filename)
    lines = []
    linenos = []
    for lineno in range(error_lineno - 2, error_lineno + 3):
        if 0 < lineno - 1 < len(all_lines):
            linenos.append(lineno)
            lines.append(all_lines[lineno - 1])

    code = ''.join(lines)
    code_lines = textwrap.dedent(code).splitlines(False)
    line_length = len(max(code_lines, key=len))
    code_lines = [code_line.ljust(line_length) for code_line in code_lines]
    return zip(linenos, code_lines)


def show_traceback(exception=None, master=None):
    if master is None:
        parent = Tk()
        parent.withdraw()
    else:
        parent = master
    if exception is None:
        exception = sys.exc_info()[1]
    window = TracebackPlusWindow(parent)
    window.show_traceback(exception)
    if master is None:
        parent.mainloop()
    else:
        master.wait_window(window)


def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_tb)
    show_traceback(exc_value)


def set_hook():
    sys.excepthook = excepthook
