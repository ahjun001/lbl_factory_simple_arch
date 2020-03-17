#!/usr/bin/env python3
# p2_select_templates.py
import os
import pathlib
import shutil
from tkinter.filedialog import askopenfilename

import p0_menus as p
import p1_select_contract as p1

p0_root_abs_dir = os.path.dirname(os.path.abspath(__file__))  # root directory where the program is located

p2_templates_l = [
    'a.Outer_box_外箱',
    'b.Inner_box_内盒',
    'c.Inside_box_中箱',
    'd.Prod_packaging_产品包装',
    'e.Plastic_bag_塑料袋',
    'f.Prod_sticker_产品上不干胶',
]

p2_default_templates_l = [
    'a.Outer_box_外箱',
    'f.Prod_sticker_产品上不干胶',
]


def add_templates_from_list(list_l, ask_questions):
    new_temp_abs_dir = ''
    # read existing templates
    drs = p1.read_dirs(p1.p1_cntrct_abs_dir)
    # make a candidate set of templates to be added
    candidates_l = []
    if drs:
        for lg in list_l:
            if lg not in drs:
                candidates_l.append(lg)
    else:
        candidates_l = list(list_l)

    if ask_questions:
        select_templates_context_func(prompt = False)
        print('>>> Select # in front of the template name to be added:\n')
        for i in range(len(candidates_l)):
            print(str(i) + '. ' + candidates_l[i][2:])
        while True:
            s = input('\nEnter nr of directory to be created, \'b\' to return : ')
            if s == 'b':
                os.system('clear')
                break
            else:
                try:
                    s_i = int(s)
                    if s_i in range(len(candidates_l)):
                        new_temp_abs_dir = os.path.join(p1.p1_cntrct_abs_dir, candidates_l[s_i])
                        create_template_dir(candidates_l[s_i])
                        break
                    else:
                        print('Integer, but not an option, try again')
                except ValueError:
                    print('That\'s not an integer, try again')

        print('~~~ Select a template svg file in the graphic file browser -- mind the browser window could be hidden')
        ini_svg = askopenfilename()
        if not ini_svg:
            return False
        # split path and filename
        path, filename_ext = os.path.split(ini_svg)
        # split filename and extension
        filename, ext = os.path.splitext(filename_ext)
        # check extension indeed is '.svg'
        if ext == '.svg':
            shutil.copy(ini_svg, os.path.join(new_temp_abs_dir, 'label_template.svg'))
        else:
            print(f'\nSelected file {filename} extension is not \'.svg\'\n')
            return False

        # copy 'template-info.json' file from same directory if it exists
        p3_f = os.path.join(path, 'template-info.json')
        if pathlib.Path(p3_f).exists():
            shutil.copy(p3_f, new_temp_abs_dir)
        return True

    else:
        for c in candidates_l:
            create_template_dir(c)


def create_default_templates():
    drs = p1.read_dirs(p1.p1_cntrct_abs_dir)
    if not drs:
        add_templates_from_list(p2_default_templates_l, ask_questions = False)


def load_n_display():
    p1.display_dirs(p1.p1_cntrct_abs_dir)


def p2_load_templates_info_l():  # used in p3
    return p1.read_dirs(p1.p1_cntrct_abs_dir)


def add_new_template():
    add_templates_from_list(p2_templates_l, ask_questions = True)


def delete_existing_template():
    print('~~~ Deleting templates non-empty directory data')
    drs = p1.read_dirs(p1.p1_cntrct_abs_dir)
    if not drs:
        return
    for i in range(len(drs)):
        print(i, drs[i][2:])
    print('~~~')
    while True:
        s = input('Enter nr of template to delete, \'b\' to return:\n')
        if s == 'b':
            os.system('clear')
            break
        else:
            try:
                s_i = int(s)
                if s_i in range(len(drs)):
                    shutil.rmtree(os.path.join(p1.p1_cntrct_abs_dir, drs[s_i]))
                    break
                else:
                    print('Integer, but not an option, try again')
            except ValueError:
                print('That\'s not an integer, try again')


def create_template_dir(dr):
    lbl_abs_dir = os.path.join(p1.p1_cntrct_abs_dir, dr)
    if not pathlib.Path(lbl_abs_dir).exists():
        os.mkdir(lbl_abs_dir, mode = 0o700)


def select_templates_context_func(prompt = True):
    print('~~~ Step 2: Selecting templates to print ~~~')
    print('Editing contract #: ', p1.p1_d["cntrct_nr"] if p1.p1_d["cntrct_nr"] else None)
    print('\nTemplates already added:')
    if not p1.display_dirs(p1.p1_cntrct_abs_dir):
        print('None added yet')
    print(60 * '-', '\n\n')
    if prompt:
        print('\n>>> Select action: ')


context_func_d = {
    'p2_select_templates': select_templates_context_func,
    'debug': select_templates_context_func,
}


def step_2__select_templates_to_print_选择_编辑标签类型():
    # make sure p1 has been run
    if not p1.load_contract_info_d():
        print('p1 has not run successfully')

    # initializing menus last, so that context functions display most recent information
    p.menu = 'p2_select_templates'
    # p.mod_lev_1_menu = p.menu
    if not p.main_menu:
        p.main_menu = p.menu
    p.menus = {
        p.menu: {
            '1': create_default_templates,
            '2': add_new_template,
            '3': delete_existing_template,
            'b': p.back_to_main_退到主程序,
            'q': p.normal_exit_正常出口,
            'd': p.debug,
        },
        'debug': {
            '2': load_n_display,
            'b': p.back_后退,
            'q': p.normal_exit_正常出口,
        },
    }
    if not p.main_menus:
        p.main_menus = p.menus
    if __name__ == '__main__':
        p.mod_lev_1_menu = p.menu
        p.mod_lev_1_menus = p.menus
    p.context_func_d = {**p.context_func_d, **context_func_d}


def main():
    """ Driver """
    step_2__select_templates_to_print_选择_编辑标签类型()
    p.run()


if __name__ == '__main__':
    main()
