#!/usr/bin/env python3
# p1_select_contract.py
import json
import os
import pathlib
import pprint
import re
import shutil
import sys
from tkinter.filedialog import askopenfilename

import xlrd

import m_menus as m

# globals that don't need to be reset when a new contract is processed
p0_root_abs_dir = os.path.dirname(os.path.abspath(__file__))  # root directory where the program is located

# globals that need to be reset when a new contract is processed
all_products_to_be_processed_set = set()
doc_setup_d = {}
p1_cntrct_abs_dir = ''  # directory where a copy of the xls contract file and contract extracted data is
p1_cntrct_info_d = {}
p1_cntrct_info_f = ''
p1_d = {}
p1_search_reg_ex_l = []
p1b_indics_from_contract_l = []
p1c_prods_w_same_key_set = {}  # make a dictionary key= info, value = sets of prods with that key
p1d_common_indics_l = []
p1e_specific_fields_d_of_d = {}
prog_info_json_f = ''


def dump_program_info_json():
    global prog_info_json_f
    global p1_d
    # document the info in program-info.json
    with open(prog_info_json_f, 'w') as fw:
        json.dump(p1_d, fw, ensure_ascii = False)


def step_1__select_a_contract_选择合同号(test_contract_nr = ''):
    global p1_cntrct_abs_dir
    global p1_d

    ini_xls = ''
    # (p1_d['cntrct_nr'], p1_d['fpath_init_xls'], p1_d['file_xls']) = (None, None, None)
    print('~~~ Step 1: Selecting a contract ~~~')
    print('~~~ Select a contract xls file in the graphic file browser -- mind the browser window could be hidden')
    if test_contract_nr:
        path = './contract_samples/' + test_contract_nr
        _, _, files = next(os.walk(path))
        for file in files:
            path_f, file_ext = os.path.split(file)
            _, ext = os.path.splitext(file_ext)
            if ext == '.xls':
                ini_xls = os.path.join('./contract_samples/' + test_contract_nr, file)
        pass
    else:
        ini_xls = askopenfilename()
    if not ini_xls:
        return False
    # split path and filename
    path, filename_ext = os.path.split(ini_xls)
    # split filename and extension
    filename, ext = os.path.splitext(filename_ext)
    # check extension indeed is '.xls'
    if ext == '.xls':
        # extract contract_nr
        s = re.match(r'\w+-\d+', filename).group()
        if s:
            print(f"Processing {s}")
            p1_d['cntrct_nr'] = s
            p1_cntrct_abs_dir = os.path.join(p0_root_abs_dir + '/data/' + p1_d['cntrct_nr'])
            if not pathlib.Path(p1_cntrct_abs_dir).exists():
                os.mkdir(p1_cntrct_abs_dir, mode = 0o700)
                # do not overwrite an existing contract file
            p1_d['file_xls'] = filename_ext
            p1_d['fpath_init_xls'] = ini_xls
            filename = os.path.join(p0_root_abs_dir + '/data/' + p1_d['cntrct_nr'], p1_d['file_xls'])
            if not pathlib.Path(filename).exists():
                shutil.copy(p1_d['fpath_init_xls'], p1_cntrct_abs_dir)

            dump_program_info_json()
            # copy setup file if exists
            stpf_rel_f = p1_d['cntrct_nr'] + '_doc_setup.json'
            stpf_abs_src = os.path.join(path, stpf_rel_f)
            stpf_abs_dest = os.path.join(p1_cntrct_abs_dir, stpf_rel_f)
            if pathlib.Path(stpf_abs_src).exists():
                if not pathlib.Path(stpf_abs_dest).exists():
                    shutil.copy(stpf_abs_src, p1_cntrct_abs_dir)

                # also copy template directories, svg and json files that might exists
            _, dirs, _ = next(os.walk(path))
            if dirs:
                for some_dir in dirs:
                    dest_dir = p1_cntrct_abs_dir + '/' + some_dir
                    if not pathlib.Path(dest_dir).exists():
                        shutil.copytree(path + '/' + some_dir, dest_dir)
            process_selected_contract()
            return True
        else:  # the prefix has not been checked
            print('A prefix could not be read from filename ext')
            return False
    else:
        print(f'\nSelected file {filename} extension is not \'.xls\'\n')
        return False


def load_o_create_program_info_d():
    """
    Loads p1_d['cntrct_nr'], p1_d['file_xls'], and p1_cntrct_abs_dir from program-info.json
    Test:
    (i) json and file already in repository
    (ii) re-create from initial file as per contract-info.json
    (iii) point at file
    """
    global prog_info_json_f
    global p1_d
    global p1_cntrct_abs_dir

    # If the data directory does not exist, create it
    data_abs_dir = os.path.join(p0_root_abs_dir, 'data')
    if not pathlib.Path(data_abs_dir).exists():
        os.mkdir(data_abs_dir, mode = 0o700)

    prog_info_json_f = os.path.join(p0_root_abs_dir, 'program-info.json')
    if pathlib.Path(prog_info_json_f).exists():
        # then load the info from (i) the repository
        # or (ii) re-create it from the initial file
        with open(prog_info_json_f) as f:
            p1_d = json.load(f)
        if 'cntrct_nr' in p1_d.keys():
            p1_cntrct_abs_dir = p0_root_abs_dir + f'/data/{p1_d["cntrct_nr"]}'
            if not pathlib.Path(p1_cntrct_abs_dir).exists():
                print(f"|\n| Cannot access {p1_cntrct_abs_dir} directory as in 'program-info.json', creating one\n|")
                os.mkdir(p1_cntrct_abs_dir, mode = 0o700)
            if 'file_xls' in p1_d.keys():
                file_xls = os.path.join(p0_root_abs_dir + '/data/' + p1_d['cntrct_nr'], p1_d['file_xls'])
                if pathlib.Path(file_xls).exists():
                    file_json = os.path.join(
                        p0_root_abs_dir + '/data/' + p1_d['cntrct_nr'],
                        p1_d['cntrct_nr'] + '_doc_setup.json'
                    )
                    if pathlib.Path(file_json).exists():
                        return True  # (i) json and file already in repository
                    else:
                        # create a _doc_setup.json with default values
                        print(f"|\n| {p1_d['cntrct_nr']}_doc_setup.json not found, creating one with default values\n|")
                        load_o_create_doc_set_up()
                else:
                    print(f"|\n| Cannot access '{file_xls}'\n|")
            else:
                print(f'program-info.json does not contain {p1_cntrct_abs_dir} data')
            print('| Trying to build from fpath_init_xls file in program-info.json')
            if 'fpath_init_xls' in p1_d.keys():
                if pathlib.Path(p1_d['fpath_init_xls']).exists():
                    shutil.copy(p1_d['fpath_init_xls'], p1_cntrct_abs_dir)
                    path, p1_d['file_xls'] = os.path.split(p1_d['fpath_init_xls'])

                    # copy setup file if exists
                    stpf_rel_f = p1_d['cntrct_nr'] + '_doc_setup.json'
                    stpf_abs_src = os.path.join(path, stpf_rel_f)
                    stpf_abs_dest = os.path.join(p1_cntrct_abs_dir, stpf_rel_f)
                    if pathlib.Path(stpf_abs_src).exists() and pathlib.Path(stpf_abs_dest).exists():
                        shutil.copy(stpf_abs_src, p1_cntrct_abs_dir)

                    # also copy template directories, svg and json files that might exists
                    _, dirs, _ = next(os.walk(path))
                    if dirs:
                        for some_dir in dirs:
                            shutil.copytree(path + '/' + some_dir, p1_cntrct_abs_dir + '/' + some_dir)
                    doc_setup_f_ini = os.path.join(path, p1_d['cntrct_nr'] + '_doc_setup.json')
                    if pathlib.Path(doc_setup_f_ini).exists():
                        shutil.copy(doc_setup_f_ini, p1_cntrct_abs_dir)
                    process_selected_contract()
                    return True  # (ii) re-create from initial file as per contract-info.json
                else:
                    print(
                        f"|\n| Cannot access '{p1_d['fpath_init_xls']}' as in 'program-info.json, no such file'\n|")
            else:
                print(f"program-info.json does not contain {p1_d['fpath_init_xls']} data")

        else:
            print(f'program-info.json does not contain {p1_d["cntrct_nr"]} data')
    else:
        print(f'{prog_info_json_f} does not exist, no such file')
    # if select then return true
    step_1__select_a_contract_选择合同号()
    return True  # (iii) point at file


def load_contract_info_d():
    """
    Loads p1_cntrct_info_f into p1_cntrct_info_d, maybe resetting these values
    Will run p1.step_2__select_templates_to_print_选择_编辑标签类型() and p1.process_default_contact() if necessary
    """
    global p1_cntrct_info_d
    global p1_cntrct_info_f
    global p1_cntrct_abs_dir

    if not load_o_create_program_info_d():
        exit()
    else:
        if not p1_cntrct_abs_dir or 'cntrct_nr' not in p1_d.keys():
            process_selected_contract()
    with open(os.path.join(p1_cntrct_abs_dir, '.' + p1_d['cntrct_nr'] + '_contract-info.json')) as fi:
        p1_cntrct_info_d = json.load(fi)
    return True


def display_or_load_output_overview():
    if load_contract_info_d():
        display()


def display():
    if p1_cntrct_info_d:
        display_p1_cntrct_info_d()
    elif p1_cntrct_info_f:
        print('trying to read_program_info from disk:')
        display_p1_program_info_f()
    else:
        print('p1 has not run or data cannot be loaded from disk:')


def delete_all_data_on_selected_contract():
    global p1_d
    global p0_root_abs_dir
    print('~~~ deleting non-empty directories ~~~')
    drs = read_dirs(p0_root_abs_dir + '/data/')
    if not drs:
        return
    for i in range(len(drs)):
        print(i, drs[i])
    print('~~~')
    while True:
        s = input('Enter nr of directory to delete_all_data_on_selected_contract, \'b\' to return : ')
        if s == 'b':
            os.system('clear')
            break
        else:
            try:
                s_i = int(s)
                if s_i in range(len(drs)):
                    if drs[int(s)] == p1_d['cntrct_nr']:
                        print(
                            '\n\t!!! Erasing current directory\n'
                            '\tthis will also delete_all_data_on_selected_contract program-info.json\n'
                            '\tand start as if repository is empty !!!'
                        )
                        os.remove(os.path.join(p0_root_abs_dir, 'program-info.json'))
                        p1_d = {'cntrct_nr': ''}
                    shutil.rmtree(p0_root_abs_dir + '/data/' + drs[int(s)])
                    break
                else:
                    print('Integer, but not an option, try again')
            except ValueError:
                print('That\'s not an integer, try again')


def load_p1_all_products_to_be_processed_set():
    global p1_cntrct_info_d
    global p1_cntrct_info_f
    global all_products_to_be_processed_set
    if not p1_cntrct_info_d:
        p1_cntrct_info_f = os.path.join(p1_cntrct_abs_dir, '.' + p1_d['cntrct_nr'] + '_contract-info.json')
        with open(p1_cntrct_info_f) as f1:
            p1_cntrct_info_d = json.load(f1)

    all_products_to_be_processed_set = sorted(p1_cntrct_info_d['all_products_to_be_processed_set'])
    print(all_products_to_be_processed_set)
    if all_products_to_be_processed_set:
        return True


def display_p1_all_products_to_be_processed_set():
    if load_p1_all_products_to_be_processed_set():
        pprint.pprint(all_products_to_be_processed_set)


def load_p1_search_reg_ex_l():
    global p1_search_reg_ex_l

    with open(os.path.join(p0_root_abs_dir + '/common', 'indicators.json')) as f:
        p1_search_reg_ex_l = json.load(f)
    if p1_search_reg_ex_l:
        return True


def display_p1_search_reg_ex_l():
    global p1_search_reg_ex_l

    if load_p1_search_reg_ex_l():
        pprint.pprint(p1_search_reg_ex_l)


def load_p1b_indics_from_contract_l():
    global p1b_indics_from_contract_l
    global p1_cntrct_info_d
    if not p1_cntrct_info_d:
        if not load_contract_info_d():
            print('p1 has not run successfully')
    filename = p1_cntrct_info_d['p1b_indics_from_contract_l']
    with open(os.path.join(p1_cntrct_abs_dir, filename)) as f1b:
        p1b_indics_from_contract_l = json.load(f1b)
        return True


def display_p1b_indics_from_contract_l():
    if load_p1b_indics_from_contract_l():
        pprint.pprint(p1b_indics_from_contract_l)


def display_p1c_all_relevant_data():
    global p1c_prods_w_same_key_set
    global p1_cntrct_info_d
    if not p1_cntrct_info_d:
        if not load_contract_info_d():
            print('p1 has not run successfully')
    filename = p1_cntrct_info_d['p1c_all_relevant_data']
    with open(os.path.join(p1_cntrct_abs_dir, filename)) as f1c:
        p1c_prods_w_same_key_set = f1c.read()
    print(p1c_prods_w_same_key_set)


def display_p1d_common_indics_l():
    global p1d_common_indics_l
    global p1_cntrct_info_d
    if not p1_cntrct_info_d:
        if not load_contract_info_d():
            print('p1 has not run successfully')
    filename = p1_cntrct_info_d['p1d_extract_common']
    with open(os.path.join(p1_cntrct_abs_dir, filename)) as f1d:
        p1d_common_indics_l = json.load(f1d)
    pprint.pprint(p1d_common_indics_l)


def load_p1e_specific_fields_d_of_d_n_p3_needed_vars():
    global p1e_specific_fields_d_of_d
    global p1_cntrct_info_d
    if not p1_cntrct_info_d:
        if not load_contract_info_d():
            print('p1 has not run successfully')
    filename = p1_cntrct_info_d['p1e_extract_specifics']
    with open(os.path.join(p1_cntrct_abs_dir, filename)) as f1e:
        p1e_specific_fields_d_of_d = json.load(f1e)
    if p1e_specific_fields_d_of_d:
        return True


def display_p1e_specific_fields_d_of_d():
    if load_p1e_specific_fields_d_of_d_n_p3_needed_vars():
        pprint.pprint(p1e_specific_fields_d_of_d)


def load_o_create_doc_set_up():
    global p1_cntrct_abs_dir
    global p1_d
    global doc_setup_d

    filename = os.path.join(p1_cntrct_abs_dir, p1_d['cntrct_nr'] + '_doc_setup.json')
    if pathlib.Path(filename).exists():
        with open(filename) as f:
            doc_setup_d = json.load(f)
    else:
        doc_setup_d['margin_w'] = 15
        doc_setup_d['margin_h'] = 15
        doc_setup_d['cover_page'] = True
        doc_setup_d['page_1_vert_offset'] = 0
        with open(filename, 'w') as f:
            json.dump(doc_setup_d, f, ensure_ascii = False)


def display_p1_cntrct_info_d():
    global p1_cntrct_info_d
    print('~~~ Reading contract-info global value ~~~')
    pprint.pprint(p1_cntrct_info_d)
    print('~~~ Finished reading contract-info global value ~~~')


def display_p1_cntrct_info_f():
    # global p1_cntrct_info_f
    # p1_cntrct_info_f = os.path.join(p1_cntrct_abs_dir, p1_d['cntrct_nr'] + '_contract-info.json')
    if p1_cntrct_info_f:
        if os.path.isfile(p1_cntrct_info_f):
            print('~~~ Reading contract-info.json file contents ~~~')
            with open(p1_cntrct_info_f) as f:
                # print(f.read_program_info())
                pprint.pprint(f.read())
            print('~~~ File contract-info.json closed ~~~')
    else:
        print(f'\nFile {p1_cntrct_info_f} not built yet\n')


def display_p1_program_info_d():
    global p1_d
    print('~~~ Reading program-info global value ~~~')
    pprint.pprint(p1_d)
    print('~~~ Finished reading program-info global value ~~~')


def display_p1_program_info_f():
    global prog_info_json_f
    print('~~~ Reading program-info.json file contents')
    with open(prog_info_json_f) as f:
        pprint.pprint(f.read())
    print('File program-info.json closed ~~~')


def read_dirs(walk_abs_dir):
    global p1_cntrct_abs_dir

    if walk_abs_dir:
        _, dirs, _ = next(os.walk(walk_abs_dir))
        if dirs:
            dirs.sort()
            dirs[:] = [d for d in dirs if d[0] not in ['.', '_']]
            return dirs
    return None


def display_dirs(walk_abs_dir):
    drs = read_dirs(walk_abs_dir)
    if drs:
        for dr in drs:
            print(dr)
        return True
    else:
        return False


def dump_contract_info_json(key, filename):
    global p1_cntrct_info_d
    global p1_cntrct_abs_dir
    p1_cntrct_info_d[key] = filename
    f = os.path.join(p1_cntrct_abs_dir, p1_cntrct_info_f)
    with open(f, 'w') as fi:
        json.dump(p1_cntrct_info_d, fi, ensure_ascii = False)


def process_selected_contract():
    global p1_cntrct_info_f
    global p1_cntrct_info_d
    global p1_cntrct_abs_dir
    global prog_info_json_f
    global p1_d
    global p1_search_reg_ex_l
    global p1b_indics_from_contract_l
    global p1c_prods_w_same_key_set
    global all_products_to_be_processed_set
    global p1d_common_indics_l
    global p1e_specific_fields_d_of_d
    # reset to zero if these had been loaded from disk before
    p1_search_reg_ex_l = []
    p1b_indics_from_contract_l = []
    p1c_prods_w_same_key_set = {}
    all_products_to_be_processed_set = set()
    p1d_common_indics_l = []
    p1e_specific_fields_d_of_d = {}

    p1_cntrct_info_f = '.' + p1_d['cntrct_nr'] + '_contract-info.json'
    filename = os.path.join(p1_cntrct_abs_dir, p1_cntrct_info_f)
    if pathlib.Path(filename).exists():
        with open(filename) as fi:
            p1_cntrct_info_d = json.load(fi)
    else:
        p1_cntrct_info_d = {}

    # the name of the -contract.json file can now be set
    rel_path_contract_json_f = '.p1a_' + p1_d['cntrct_nr'] + '-contract.json'

    # Creating the json file from the local xls file: opening the xl file
    book = xlrd.open_workbook(
        os.path.join(p1_cntrct_abs_dir, p1_d['file_xls']))
    sheet = book.sheet_by_index(0)

    row = 0
    while not sheet.col_values(0, 0)[row]:  # getting to last row before D1 in col. A
        row += 1

    # get global info
    if sheet.cell(1, 7).value[0:4] == '合同编号':
        contract_json_d = {'合同编号': sheet.cell(1, 7).value[5:].strip()}  # select data from cell 'H2'
    else:
        sys.exit("Error reading contract XLS file:  expecting to select 合同编号 in cell 'H2'")

    non_decimal = re.compile(r'[^\d.]+')  # necessary to clean formatting characters in XLS cells

    contract_json_d['l_i'] = []
    while sheet.col_values(0, 0)[row]:  # looping while there is product information available
        prod_n = sheet.cell(row, 1).value  # correcting XL showing an int but passing a float,
        # all prod # are not numbers
        if isinstance(prod_n, float):
            prod_n = str(int(prod_n))
        tmp_dict = {  # use to be OrderedDict for human readability, not necessary for program
            "01.TST_prod_#-需方产品编号": prod_n,
            "02.Sup_prod_#-供方产品编号": sheet.cell(row, 2).value,
            "03.Prod_spec-产品规格": sheet.cell(row, 3).value,
            "04.Prod_name-产品名称": sheet.cell(row, 4).value,
            "05.Quantity-数量": sheet.cell(row, 5).value,
            "06.Units-单位": sheet.cell(row, 6).value,
            "07.Unit_price-单价": float(non_decimal.sub('', sheet.cell(row, 7).value[3:])),
            "08.Total_price-全额": float(non_decimal.sub('', sheet.cell(row, 8).value[3:])),
            "09.Tech_spec-技术参数_1": sheet.cell(row + 1, 2).value,
            "10.Tech_spec-技术参数_2": sheet.cell(row + 1, 7).value,
            "11.Pack_spec-包装要求": sheet.cell(row + 2, 2).value
        }
        contract_json_d['l_i'].append(dict(tmp_dict))
        row += 3

    with open(os.path.join(p1_cntrct_abs_dir, rel_path_contract_json_f), 'w') as fc:
        json.dump(contract_json_d, fc, ensure_ascii = False)
    # populate p1_cntrct_info_d: a structure to store template information, and its corresponding json file
    p1_cntrct_info_d['p1a_contract_json'] = rel_path_contract_json_f

    load_p1_search_reg_ex_l()

    # p1b_indics_from_contract_l: harvesting all indicators possibly available in the contract_json_d
    for row_indic in p1_search_reg_ex_l:
        what = row_indic['what']
        how = row_indic['how']
        for prod in contract_json_d['l_i']:  # inspecting products one by one
            tmp_dct = {  # adding 03.Prod_spec-产品规则 info
                'what': 'xl_prod_spec',
                'where': 'xl_quantity-数量',
                'prod_nr': prod['01.TST_prod_#-需方产品编号'],
                'info': prod["03.Prod_spec-产品规格"]
            }
            p1b_indics_from_contract_l.append(tmp_dct)
            tmp_dct = {  # adding 05.Quantity-数量 info
                'what': 'total_qty',
                'where': 'xl_quantity-数量',
                'prod_nr': prod['01.TST_prod_#-需方产品编号'],
                'info': int(prod['05.Quantity-数量'])
            }
            p1b_indics_from_contract_l.append(tmp_dct)
            for key, value in prod.items():  # looping over each xl field, searching its value
                if isinstance(value, str):  # ignore 05.Qty, 07.Unit_price, and 08.Total_price
                    s_tmp = re.findall(how, value)
                    if s_tmp:  # if this test succeeds then info must be registered
                        srch = []
                        for s in s_tmp:
                            srch.append(s.strip())  # strip the search result
                        for indication in srch:
                            tmp_dct = {
                                'what': what,  # from indicators.json : pack, kg, mm, 牌, v_Hz, plstc_bg
                                'where': key,  # xl cell: 10.Tech_spec-技术参数_2
                                'info': indication,  # 1.00    = indic
                                'prod_nr': prod["01.TST_prod_#-需方产品编号"],  # 1050205001#
                            }
                            p1b_indics_from_contract_l.append(tmp_dct)
        p1b_indics_from_contract_l.sort(key = lambda item: item['prod_nr'])
        file_indics = '.p1b_' + p1_d['cntrct_nr'] + '_indics_from_contract_l.json'

        # register in file and object
        dump_contract_info_json('p1b_indics_from_contract_l', file_indics)

        f = os.path.join(p1_cntrct_abs_dir, file_indics)
        with open(f, 'w') as f:
            json.dump(p1b_indics_from_contract_l, f, ensure_ascii = False)

        # p1c_prods_w_same_key_set = {}  # make a dictionary key= info, value = sets of prods with that key
        for row in p1b_indics_from_contract_l:
            # for index, row in c_df.iterrows():  # index is not used
            if (row['what'], row['where'], row['info']) not in p1c_prods_w_same_key_set.keys():
                p1c_prods_w_same_key_set[(row['what'], row['where'], row['info'])] = set()
            p1c_prods_w_same_key_set[(row['what'], row['where'], row['info'])].add(row['prod_nr'])

            # document in all_relevant_data_json
    p1c_file_out_f = '.p1c_' + p1_d['cntrct_nr'] + '_all_relevant_data.txt'
    f = os.path.join(p1_cntrct_abs_dir, p1c_file_out_f)
    with open(f, 'w') as f1c:
        # json.dump(p1c_prods_w_same_key_set, f1c, ensure_ascii = False) won't work
        # f1c.write(p1c_prods_w_same_key_set.__str__()) doesn't look pretty
        pprint.PrettyPrinter(indent = 2, stream = f1c).pprint(p1c_prods_w_same_key_set)

    dump_contract_info_json('p1c_all_relevant_data', p1c_file_out_f)

    # p1c_build_set_of_all_products_to_be_processed
    for prod in contract_json_d['l_i']:
        all_products_to_be_processed_set.add(prod["01.TST_prod_#-需方产品编号"])
    dump_contract_info_json('all_products_to_be_processed_set', sorted(list(all_products_to_be_processed_set)))

    # p6_split_between p6_common_indics and p6_specific_indics
    for k, v in p1c_prods_w_same_key_set.items():
        # indic is not a  packing quantity and is common to all products
        if k[0] not in ['pack', 'parc', 'u_parc'] and v == all_products_to_be_processed_set:
            p1d_common_indics_l.append(k)
        else:
            for prod in v:
                if p1e_specific_fields_d_of_d.get(prod) is None:
                    p1e_specific_fields_d_of_d[prod] = {}
                p1e_specific_fields_d_of_d[prod][k[0]] = k[2]  # prod_n : 'what' = indic

    # Checking that numbers are coherent before storing or displaying
    for k, v in p1e_specific_fields_d_of_d.items():
        # Checking that packing quantities info are coherent with total_quantity, if not: exit with a message
        if v['total_qty'] != int(v['parc']) * int(v['u_parc']):  # * int(float(v['pack'])):
            print(60 * '*' + '\nIncoherent quantities in xls contract in product: ' + k + '\n' + 60 * '*')
            exit()
        # Checking that under_packing are multiple of parcels (boxes are full), if not: exit the program with a
        # message
        if int(v['u_parc']) % int(float(v['pack'])) != 0:
            print(60 * '*' + '\nUnder-parcels not full in xls contract in product: ' + k + '\n' + 60 * '*')
            exit()

    # indicators common to all products: write to file
    filename = '.p1d_' + p1_d['cntrct_nr'] + '_extract_common.json'
    f = os.path.join(p1_cntrct_abs_dir, filename)
    with open(f, 'w') as p1d_f:
        json.dump(p1d_common_indics_l, p1d_f, ensure_ascii = False)

    dump_contract_info_json('p1d_extract_common', filename)

    # indicators specific to one or more products, but not to all: print p1e_specific_fields_d_of_d
    filename = '.p1e_' + p1_d['cntrct_nr'] + '_extract_specifics.json'
    f = os.path.join(p1_cntrct_abs_dir, filename)
    with open(f, 'w') as p1e_f:
        json.dump(p1e_specific_fields_d_of_d, p1e_f, ensure_ascii = False)

    dump_contract_info_json('p1e_extract_specifics', filename)

    # define page setup
    load_o_create_doc_set_up()

    # document in A1234-456_contract-info.json
    filename = os.path.join(p1_cntrct_abs_dir, p1_cntrct_info_f)
    with open(filename, 'w') as fi:
        json.dump(p1_cntrct_info_d, fi, ensure_ascii = False)


def select_contract_main_context_func():
    print('~~~ Now editing contract #: ', p1_d['cntrct_nr'] if 'cntrct_nr' in p1_d.keys() else 'None selected')
    print('>>> Select action: ')


def select_contract_debug_func():
    display_dirs(p0_root_abs_dir + '/data/')
    print('~~~ Select contract / Display ~~~')


context_func_d = {
    'init': select_contract_main_context_func,
    'debug': select_contract_debug_func,
}


def init():
    load_o_create_program_info_d()

    # initializing menus last, so that context functions display most recent information
    m.menu = 'init'
    if not m.main_menu:
        m.main_menu = m.menu
    m.menus = {
        m.menu: {
            '1': step_1__select_a_contract_选择合同号,
            '2': delete_all_data_on_selected_contract,
            '3': process_selected_contract,
            'b': m.back_to_main_退到主程序,
            'q': m.normal_exit_正常出口,
            'd': m.debug,
        },
        'debug': {
            '1': display_p1_program_info_d,
            '2': display_p1_program_info_f,
            '3': load_o_create_program_info_d,
            '5': display_p1_search_reg_ex_l,
            '6': display_p1_all_products_to_be_processed_set,
            '7': display_p1b_indics_from_contract_l,
            '8': display_p1c_all_relevant_data,
            '9': display_p1d_common_indics_l,
            'a': display_p1e_specific_fields_d_of_d,
            'b': m.back_后退,
            'q': m.normal_exit_正常出口,
        },
    }
    if not m.main_menus:
        m.main_menus = m.menus
    if __name__ == '__main__':
        m.mod_lev_1_menu = m.menu
        m.mod_lev_1_menus = m.menus
    m.context_func_d = {**m.context_func_d, **context_func_d}


def main():
    """ Driver """
    init()
    m.run()


if __name__ == '__main__':
    main()
