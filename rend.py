import argparse
import glob
import http.server
import jinja2
import mimetypes
import os
import sys
import shutil
import termcolor
import yaml

BUILD_FOLDER = "www"
HOST_AND_PORT = ("localhost", 9000)


def print_error_and_die(error_message):
    termcolor.cprint(error_message, "red")
    sys.exit(1)


def normalize_regexp(regexp_or_maybe_not, root):
    if ("?" in regexp_or_maybe_not) or ("*" in regexp_or_maybe_not):
        return regexp_or_maybe_not
    if os.path.isdir(os.path.join(root, regexp_or_maybe_not)):
        return os.path.join(regexp_or_maybe_not, "**/*")
    else:
        return regexp_or_maybe_not


def read_conf(root):
    config_path = os.path.join(root, "rend.conf")
    if not os.path.exists(config_path):
        print_error_and_die("Cannot find configuration file at {}".format(config_path))
    lines = [x.strip() for x in open(config_path, "r", encoding="utf-8").readlines()]
    groups = [[]]
    for line in lines:
        if (line == "") or (line.startswith("#")):
            if len(groups[-1]) > 0:
                groups.append([])
        else:
            groups[-1].append(line)
    if (len(groups) == 0) or (len(groups[0]) == 0):
        print_error_and_die("Configuration file at {} seems to be (kinda) empty".format(config_path))
    to_render = []
    to_copy = set()
    for g in groups:
        if (g[0] == "@@") and (len(g) in [3, 4]):  # Page to render
            render_item = list(g[1:])
            if len(render_item) == 2:
                render_item.insert(1, None)
            to_render.append(tuple(render_item))
        elif (g[0] == ">>") and (len(g) > 1):  # Asset to copy
            for regexp_or_maybe_not in g[1:]:
                norm_regexp = normalize_regexp(regexp_or_maybe_not, root)
                norm_regexp_match = glob.glob(os.path.join(root, norm_regexp), recursive=True)
                norm_regexp_match_files_only = [x for x in norm_regexp_match if not os.path.isdir(x)]
                to_copy.update(norm_regexp_match_files_only)
        else:
            print_error_and_die("Corrupted configuration around lines:\n~~~~\n{}\n~~~~".format("\n".join(g)))
    return to_render, to_copy


def cleanup_build_folder(build_folder):
    try:
        if os.path.exists(build_folder):
            shutil.rmtree(build_folder, ignore_errors=False)
        os.mkdir(build_folder)
    except Exception as ex:
        print_error_and_die("Cannot cleanup build folder at {} due to {}".format(build_folder, ex))


def render_single_page(root, build_folder, yaml_rel_path, j2_rel_path, output_rel_path):
    output_abs_path = os.path.join(build_folder, output_rel_path)
    yaml_obj = {}
    if yaml_rel_path is not None:
        yaml_abs_path = os.path.join(root, yaml_rel_path)
        try:
            yaml_obj = yaml.load(open(os.path.join(root, yaml_rel_path), "r"), Loader=yaml.FullLoader)
        except Exception as ex:
            print_error_and_die("[-] Cannot load  YAML data at {} due to ".format(yaml_abs_path, ex))
    try:
        j2_obj = jinja2.Environment(
            loader=jinja2.FileSystemLoader(".", followlinks=False),
            undefined=jinja2.StrictUndefined).get_template(j2_rel_path)
        html = j2_obj.render(yaml_obj)
        os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)
        open(output_abs_path, "w", encoding="utf-8").write(html)
    except jinja2.TemplateNotFound as ex:
        print_error_and_die("[-] Cannot render Jinja2 template due to {}".format(ex))
    except Exception as ex:
        print_error_and_die("[-] Failed to save file to {} due to {}!".format(output_abs_path, ex))
    termcolor.cprint("[+] Page rendered and saved to {}".format(output_abs_path), "green")


def copy_single_asset(root, build_folder, src_path):
    dst_path = os.path.join(build_folder, os.path.relpath(src_path, root))
    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy(src_path, dst_path)
    except Exception as ex:
        print_error_and_die("[-] Failed to copy {} to {} due to {}".format(src_path, dst_path, ex))
    termcolor.cprint("[+] Copied {} to {}".format(src_path, dst_path), "cyan")


def build():
    root = os.path.dirname(sys.argv[0])
    to_render, to_copy = read_conf(root)
    build_folder = os.path.join(root, BUILD_FOLDER)
    cleanup_build_folder(build_folder)
    for j2_rel_path, yaml_rel_path, output in to_render:
        render_single_page(root, build_folder, yaml_rel_path, j2_rel_path, output)
    for path in to_copy:
        copy_single_asset(root, build_folder, path)
    termcolor.cprint("Rendered {:d} pages, copied {:d} assets".format(len(to_render), len(to_copy)), "grey")


class RendRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        root = os.path.dirname(sys.argv[0])
        to_render, _ = read_conf(root)
        if self.path == "/":
            wanted_file = "index.html"
        else:
            wanted_file = self.path[1:]
        path = os.path.join(root, BUILD_FOLDER, wanted_file)
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            termcolor.cprint("Ups... Cannot find file {}. Regenerate site, maybe?".format(path), "red")
        else:
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(path)[0])
            self.end_headers()
            self.wfile.write(open(path, "rb").read())


def serve():
    server = http.server.HTTPServer(HOST_AND_PORT, RendRequestHandler)
    try:
        print("Running server at {}:{:d}... Press Ctrl+C to terminate".format(HOST_AND_PORT[0], HOST_AND_PORT[1]))
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped due to keyboard interrupt!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="REND - minimalistic static website generator (version 1.20)")
    parser.add_argument("task", nargs="?", default="build", help="\"build\" or \"serve\"")
    args = parser.parse_args()
    if args.task == "build":
        build()
    elif args.task == "serve":
        serve()
    else:
        print_error_and_die("Unknown task, should be \"build\" or \"serve\"")
