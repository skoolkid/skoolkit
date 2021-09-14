from skoolkit.skoolhtml import HtmlWriter

def init_page(self, skoolkit, game):
    path = skoolkit['path']
    if skoolkit['page_id'].startswith('Asm-'):
        asm_path, sep, asm_page = path.rpartition('/')
        addr_str = asm_page[:-5]
        if self.base == 16:
            path = '{}/{}.html'.format(asm_path, int(addr_str, 16))
        else:
            path = '{}/{:04X}.html'.format(asm_path, int(addr_str))
    root_path, sep, index = skoolkit['index_href'].rpartition('/')
    skoolkit['AltPath'] = f'{root_path}{sep}../{game["alt_dir"]}/{path}'

HtmlWriter.init_page = init_page
