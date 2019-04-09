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

CONFIG_FILE = "rend.conf"
BUILD_FOLDER = "www"
HOST_AND_PORT = ("localhost", 9000)


def read_config_file(root):
    config_path = os.path.join(root, CONFIG_FILE)
    if not os.path.exists(config_path):
        termcolor.cprint("Cannot find configuration file at {}".format(config_path), "red")
        sys.exit(1)
    lines = open(config_path, "r", encoding="utf-8").readlines()
    if len(lines) == 0:
        termcolor.cprint("Empty configuration at {}".format(config_path), "red")
        sys.exit(1)
    lines.append("")  # Not bug, but feature!
    to_render = []
    to_copy = set()
    conf_group = []
    for line_idx, line in enumerate(lines):
        norm_line = line.strip()
        if norm_line.startswith("#"):
            continue
        elif norm_line != "":
            conf_group.append(norm_line)
        elif (norm_line == "") and (len(conf_group) > 0):
            if conf_group[0] == "->":
                for copy_reg_expr in conf_group[1:]:
                    to_copy.update(glob.glob(os.path.join(root, copy_reg_expr), recursive=True))
            else:
                if len(conf_group) == 3:
                    conf_group.append(None)
                if len(conf_group) != 4:
                    termcolor.cprint("Wrong {} content around line {:d}".format(config_path, line_idx), "red")
                    sys.exit(1)
                to_render.append(tuple(conf_group))
            conf_group.clear()
    return to_render, to_copy


def cleanup_build_folder(build_folder):
    try:
        if os.path.exists(build_folder):
	        shutil.rmtree(build_folder, ignore_errors=False)
    except Exception as ex:
        termcolor.cprint("Cannot cleanup build folder at {} due to the following error {}".format(build_folder, ex))
        sys.exit(1)
    try:
        os.mkdir(build_folder)
    except Exception as ex:
        termcolor.cprint("Cannot create folder at {} due to the following error {}".format(build_folder, ex))
        sys.exit(1)


def render_single_page(root, build_folder, j2_rel_path, yaml_rel_path, output_path):
    j2_abs_path = os.path.join(root, j2_rel_path)
    if not os.path.exists(j2_abs_path):
        termcolor.cprint("[-] Cannot find Jinja2 template at {}".format(j2_abs_path), "red")
        sys.exit(1)
    try:
        j2_obj = jinja2.Environment(
            loader=jinja2.FileSystemLoader(".", followlinks=False),
            undefined=jinja2.StrictUndefined).get_template(j2_rel_path)
    except jinja2.TemplateNotFound as ex:
        termcolor.cprint("[-] Error reading Jinja2 template : {}".format(ex))
        sys.exit(1)

    yaml_abs_path = os.path.join(root, yaml_rel_path)
    if not os.path.exists(yaml_abs_path):
        termcolor.cprint("[-] Cannot find YAML data at {}".format(yaml_abs_path))
        sys.exit(1)
    try:
        yaml_obj = yaml.load(open(yaml_abs_path, "r"))
        html = j2_obj.render(yaml_obj)
    except Exception as ex:
        termcolor.cprint("[-] Cannot parse file {} due to {}!".format(yaml_abs_path, ex))
        sys.exit(1)

    output_path = os.path.join(build_folder, output_path)
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        open(output_path, "w", encoding="utf-8").write(html)
        termcolor.cprint("[+] Page created and saved to {}".format(output_path), "green")
    except Exception as ex:
        termcolor.cprint("[-] Failed to save file to {} due to {}!".format(output_path, ex))
        sys.exit(1)


def copy_single_set_of_objects(root, build_folder, path):
    rel_path = os.path.relpath(path, root)
    dest = os.path.join(build_folder, rel_path)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(path, dest)
        termcolor.cprint("[+] Copied {}".format(dest), "green")
    except Exception as ex:
        termcolor.cprint("[-] Failed to copy {} to {} due to {}".format(path, dest, ex), "red")
        sys.exit(1)


class RendRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        print("New request for {}".format(self.requestline))
        root = os.path.dirname(sys.argv[0])
        to_render, _ = read_config_file(root)
        if self.path == "/":
            wanted_file = "index.html"
        else:
            wanted_file = self.path[1:]
        for _, _, file, slug in to_render:
            if self.path == slug:
                wanted_file = file
                break
        build_folder = os.path.join(root, BUILD_FOLDER)
        path = os.path.join(build_folder, wanted_file)
        if not os.path.exists(path):
            print("Ups... Cannot find file {}. Regenerate site, maybe?".format(path))
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        mimetype = mimetypes.guess_type(path)
        self.send_header("Content-type", mimetype[0])
        self.end_headers()
        self.wfile.write(open(path, "rb").read())


def serve():
    server = http.server.HTTPServer(HOST_AND_PORT, RendRequestHandler)
    try:
        print("Running server at {}:{:d}... Press Ctrl+C to terminate!".format(HOST_AND_PORT[0], HOST_AND_PORT[1]))
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Server stopped due to keyboard interrupt")
        sys.exit()


def run_cli():
    parser = argparse.ArgumentParser(prog="REND - minimalistic static website generator")
    parser.add_argument("--serve", action="store_true", default=False, help="Starts development server")
    args = parser.parse_args()

    root = os.path.dirname(sys.argv[0])
    if args.serve:
        serve()

    to_render, to_copy = read_config_file(root)
    build_folder = os.path.join(root, BUILD_FOLDER)
    cleanup_build_folder(build_folder)

    termcolor.cprint("Generating pages...", "blue")
    for j2_rel_path, yaml_rel_path, output, _ in to_render:
        render_single_page(root, build_folder, j2_rel_path, yaml_rel_path, output)
    termcolor.cprint("Copying assets...", "blue")
    for path in to_copy:
        copy_single_set_of_objects(root, build_folder, path)

    print("Done. Rendered {:d} pages, copied {:d} files.".format(len(to_render), len(to_copy)))


if __name__ == '__main__':
    run_cli()
