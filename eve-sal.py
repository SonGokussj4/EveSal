#!/usr/bin/env python

import re
import sys
import pickle
import unicodedata
from pathlib import Path
# from pprint import pprint
from collections import defaultdict
from dataclasses import dataclass

try:
    import pdftotext
except ModuleNotFoundError:
    print("You're on windows. Importing pdftotext failed. (You can't use --convert either)")
import plotly.graph_objects as go


# =================================
# =           CONSTANTS           =
# =================================
curdir = Path('.')
BAR_WIDTH = 0.4
BAR_OFFSET = -0.4


# ===============================
# =           CLASSES           =
# ===============================
@dataclass
class Glob:
    all_dates: list = None


# =================================
# =           FUNCTIONS           =
# =================================
def fix_missing_keys(ls, all_dates):
    dates = {date[0]: date[1] for date in ls}
    fixed_ls = [(date, dates[date]) if date in dates.keys()
                else (date, '0')
                for date in all_dates]
    return fixed_ls


def strip_accents(s):
    """Return diacritic's stripped string.

    Example:
        >>> strip_accents('Růžovoučký kůň pěl ďábelské ódy')
        'Ruzovoucky kun pel dabelske ody'
    """
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def get_pdf_files(directory: Path) -> list:
    """Return list of all 'VypListek*.pdf' files in entered directory."""
    files = []
    for item in directory.iterdir():
        if not item.is_file():
            continue

        if 'VypListek' in item.name and item.suffix == '.pdf':
            files.append(item)

    return files


def fix_bad_converts(line: str) -> str:
    if 'Be z hotovostne' in line:
        line = line.replace('Be z hotovostne', 'Bezhotovostne;')
    elif 'VYPOCT . ZALOHA' in line:
        line = line.replace('VYPOCT . ZALOHA', 'VYPOCT. ZALOHA')
    elif 'EVEKT OR' in line:
        line = line.replace('EVEKT OR', 'EVEKTOR')
    return line


def process_pdfs(pdf_files: list, write_txt: bool=False) -> dict:
    """Create txt representation of .pdf files."""
    dc = {}
    for file in pdf_files:

        # Create pdfToText.PDF object --> text
        with open(file, 'rb') as f:
            pdf = pdftotext.PDF(f)
        text = '\n\n'.join(pdf)

        # Convert text into lines, strip diactitics
        converted_lines = []
        for item in text.split('\n'):
            # Replace diacritic
            line = strip_accents(item.replace(':', '').strip())
            # Reaplce long spaces with '; '
            line = re.sub(r'\s{2,}', '; ', line)
            # Fix few keys like 'Be z hotovostne' --> 'Bezhotovostne'
            line = fix_bad_converts(line)
            # print("-->", line)
            converted_lines.append(line)

        # Fill dc with {'vypListek1.txt': [line1, line2, ...]}
        txt_filename = f'{file.stem}_res.txt'
        # print("DEBUG: txt_filename:", txt_filename)
        dc[txt_filename] = converted_lines

        if write_txt:
            txt_fullpath = file.parent / txt_filename
            # print("DEBUG: txt_fullpath:", txt_fullpath.resolve())

            with open(txt_fullpath.resolve(), 'w') as f:
                converted_lines.append(f'{line}\n')
                f.writelines([f'{line}\n' for line in converted_lines])

            with open('data.db', 'wb') as f:
                pickle.dump(dc, f, pickle.HIGHEST_PROTOCOL)
    return dc


def plot_results(dc: dict=None, from_pickle: str="") -> None:
    """Using Plotly show results in bar-plot."""
    # dc = {
    #     '2017_05.txt': ['C2 KUN; EVEKT OR, spol. s r.o.', '1127; Ve rne r Jan; 05 2017', '*** HRUBA MZDA; 121212'],
    #     '2018_10.txt': ['C2 KUN; EVEKTOR, spol. s r.o.', '1127; Bc. Verner Jan; 10 2019', '*** HRUBA MZDA; 131313'],
    # }
    # dc2 = {
    #   '*** HRUBA MZDA': [(05 2017, 121212), (10 2019, 131313)],
    # }
    if from_pickle:
        with open('data.db', 'rb') as f:
            dc = pickle.load(f)

    # Fill all_dates
    Glob.all_dates = [line[1].split(';')[-1].strip() for line in dc.values()]

    dc2 = defaultdict(list)
    for ls in dc.values():
        date = ls[1].split(';')[-1].strip()
        for line in ls:
            # Ignore these keys
            if any(x in line.split(';')[0] for x in ['- - -', ':', 'PERM spol.']):
                continue
            key = line.split(';')[0].strip()
            # Skip empty keys
            if not key:
                continue
            values = ';'.join(line.split(';')[1:]).strip()
            # print("  DEBUG: values:", values)
            dc2[key].append((date, values))

    dc = dc2

    layout = go.Layout(xaxis={'type': 'category'})  # NOT convert x values into numbers

    fig = go.Figure(data=[], layout=layout)

    # ADD BARS
    add_bar(fig, dc['*** HRUBA MZDA'], 'Hrubá Mzda', main=True)
    add_bar(fig, dc['Bezhotovostne'], 'Bezhotovostně', subval=True, idx=1)
    add_bar(fig, dc['Vykonnostni odmeny'], 'Výkonnostní odměny')
    add_bar(fig, dc['Mes.premie z fondu'], 'Měs prémie z fondu')
    add_bar(fig, dc['PRUMER (dov.)'], 'Dovolená - Průměr')
    add_bar(fig, dc['DOVOLENA-zust.'], 'Dovolená - Zůstatek')
    add_bar(fig, dc['Stravne s prispevkem'], 'Stravné')
    add_bar(fig, dc['Kompenzace kapit.poj'], 'Kompenace kapit.poj', subval=True, idx=1)

    # pprint(dc)

    fig.update_layout(barmode='stack')
    fig.show()


def add_bar(fig, dc_key_ls, name=None, subval=False, idx=0, main=False):
    """Add bar."""
    # print('===  +  BAR  ========')
    # print(name)
    # pprint(dc_key_ls)

    # Case ('01 2016', '123456789/2010; 16342'),
    if subval:
        data = [(key[0], key[1].split(';')[idx]) for key in dc_key_ls]
        data = fix_missing_keys(data, Glob.all_dates)
        try:
            data_y = [int(val[1]) for val in data]
        except Exception:
            try:
                data_y = [int(round(float(val[1]), 0)) for val in data]
            except ValueError:
                name = f'(Minus) {name}'
                data_y = [int(val[1].replace('-', '')) for val in data]

    # Case ('05 2018', '2500')
    else:
        data = [(key[0], key[1]) for key in dc_key_ls]
        data = fix_missing_keys(data, Glob.all_dates)
        try:
            data_y = [int(val[1]) for val in data]
        except Exception:
            # Case ('01 2016', '143.25')
            try:
                data_y = [int(round(float(val[1]), 0)) for val in data]
            except ValueError:
                name = f'(Minus) {name}'
                data_y = [int(val[1].replace('-', '')) for val in data]

    fig.add_bar(
        name=name,
        x=[val[0] for val in data],
        y=data_y,
        text=data_y,
        textposition='auto',
        width=BAR_WIDTH,
        offset=0 if main is True else BAR_OFFSET,
        base=0 if main is True else None,
    ),


def main():
    """Main Function."""
    if len(sys.argv) == 1:
        print("ERROR: --convert (Linux) or --plot (Windows)")
        return 1

    elif sys.argv[1] == '--convert':
        pdf_files = get_pdf_files(curdir)
        process_pdfs(pdf_files, write_txt=True)

    elif sys.argv[1] == '--plot':
        plot_results(None, from_pickle=True)


if __name__ == '__main__':
    main()
