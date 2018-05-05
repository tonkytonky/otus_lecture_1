import argparse
import ast
import os
import collections

import nltk


def _main():
    args = get_args(argparse.ArgumentParser())
    nltk.download('averaged_perceptron_tagger', download_dir=args.dir)

    dirpaths = load_dirpaths(args.path)
    verbs = count_verbs_in_dirs(dirpaths)
    print_top_verbs(verbs, top_size=10)


def get_args(parser):
    parser.add_argument(
        'path',
        help='Path to directory with files to count verbs from'
    )
    parser.add_argument(
        '-d',
        '--dir',
        help='Download directory for `nltk` resource files',
        default=None
    )

    return parser.parse_args()


def load_dirpaths(base_path):
    dirs_paths = []
    for entry in os.listdir(base_path):
        entry_path = os.path.join(base_path, entry)
        if os.path.isdir(entry_path):
            dirs_paths.append(entry_path)
    return dirs_paths


def count_verbs_in_dirs(dirpaths):
    verbs_count = collections.Counter()
    for dirpath in dirpaths:
        verbs_count += count_verbs_in_dir(dirpath)
    return verbs_count


def count_verbs_in_dir(path):
    files_trees = [
        file_tree for file_tree in get_files_trees(path) if file_tree
    ]
    func_names = flatten([
        get_functions_names(file_tree) for file_tree in files_trees
    ])
    print('Functions extracted')
    verbs = flatten([
        get_verbs_from_func_name(func_name)
        for func_name in func_names
    ])
    return collections.Counter(verbs)


def get_files_trees(dirpath):
    filepaths = get_filepaths_by_extension(dirpath, '.py')
    print('Total {} files'.format(len(filepaths)))

    trees = []
    for filepath in filepaths:
        with open(filepath, 'r', encoding='utf-8') as file_handler:
            file_content = file_handler.read()
        try:
            tree = ast.parse(file_content)
        except SyntaxError as e:
            print(e)
            tree = None
        trees.append(tree)

    print('Trees generated')
    return trees


def get_filepaths_by_extension(dirpath, extension, files_from_dir=120):
    filepaths = []
    for dirname, _, filenames in os.walk(dirpath, topdown=True):
        for filtered_filename in filter_filenames(filenames, extension):
            if len(filepaths) == files_from_dir:
                break
            filepaths.append(
                os.path.join(dirname, filtered_filename))
    return filepaths


def filter_filenames(files, extension, files_from_subdir=25):
    files_count = 0
    for file in files:
        if files_count == files_from_subdir:
            break
        if file.endswith(extension):
            yield file
            files_count += 1


def get_functions_names(file_tree):
    functions_names = []
    for node in ast.walk(file_tree):
        node_name = node.name if hasattr(node, 'name') else None
        if isinstance(node, ast.FunctionDef) and not is_magic_method(node_name):
            functions_names.append(node_name.lower())
    return functions_names


def get_verbs_from_func_name(func_name):
    return [word for word in func_name.split('_') if is_verb(word)]


def is_verb(word):
    if not word:
        return False
    pos_info = nltk.pos_tag([word])
    return pos_info[0][1] == 'VB'


def is_magic_method(func_name):
    return func_name.startswith('__') and func_name.endswith('__')


def print_top_verbs(verbs, top_size):
    print('Total {verbs_len} unique verbs. Top {top_size}:'.format(
        verbs_len=len(verbs.keys()),
        top_size=top_size,
    ))
    for word, occurrence in verbs.most_common(top_size):
        print(word, occurrence)


def flatten(lst):
    for sublist in lst:
        for item in sublist:
            yield item


if __name__ == '__main__':
    _main()
