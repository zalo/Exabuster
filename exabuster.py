"""Ghost Buster. Static site generator for Ghost.
Usage:
  buster.py generate [--domain=<local-address>] [--dir=<path>] [--new-domain=<remote-address>]
  buster.py preview [--dir=<path>]
  buster.py (-h | --help)
  buster.py --version
Options:
  -h --help                         Show this screen.
  --version                         Show version.
  --dir=<path>                      Absolute path of directory to store static pages.
  --domain=<local-address>          Address of local ghost installation [default: localhost:2368].
  --new-domain=<remote-address>     Address of the remote static web location.
"""

import os
import os.path
from os import path
import re
import sys
import time
import fnmatch
import socketserver
import http.server
import codecs
from docopt import docopt
from time import gmtime, strftime
from pyquery import PyQuery

def main():
    arguments = docopt(__doc__, version='0.1.3')
    if arguments['--dir'] is not None:
        static_path = arguments['--dir']
    else:
        static_path = os.path.join(os.getcwd(), 'static')

    if arguments['generate']:
        print("Waiting for Server to Start up...")
        time.sleep(5)
        
        command = ("wget "
                   "-e robots=off "
                   "--recursive "             # follow links to download entire site
                   #"--convert-links "         # make links relative
                   "--page-requisites "       # grab everything: css / inlined images
                   "--no-parent "             # don't go to parent level
                   "--directory-prefix {1} "  # download contents to static/ folder
                   "--no-host-directories "   # don't create domain named folder
                   "--restrict-file-name=unix "  # don't escape query string
                   "{0}").format(arguments['--domain'], static_path)
        os.system(command)

        def getFile(subpath):
          base_command = "wget --convert-links --page-requisites --no-parent --directory-prefix {1} --no-host-directories --restrict-file-name=unix {0}{2}"
          command = base_command.format(arguments['--domain'], static_path, subpath)
          os.system(command)

        # copy sitemap files since Ghost 0.5.7
        getFile("/404.html")
        getFile("/sitemap.xsl")
        getFile("/sitemap.xml")
        getFile("/sitemap-pages.xml")
        getFile("/sitemap-posts.xml")
        getFile("/sitemap-authors.xml")
        getFile("/sitemap-tags.xml")

        # remove query string since Ghost 0.4
        file_regex = re.compile(r'.*?(\?.*)')
        for root, dirs, filenames in os.walk(static_path):
            for filename in filenames:
                if file_regex.match(filename):
                    newname = re.sub(r'\?.*', '', filename)
                    print("Rename", filename, "=>", newname)
                    os.rename(os.path.join(root, filename), os.path.join(root, newname))

        # remove superfluous "index.html" from relative hyperlinks found in text
        abs_url_regex = re.compile(r'^(?:[a-z]+:)?//', flags=re.IGNORECASE)
        def fixLinks(text, parser):
            d = PyQuery(bytes(bytearray(text, encoding='utf-8')), parser=parser)
            for element in d('a'):
                e = PyQuery(element)
                href = e.attr('href')
                if href is None:
                    continue
                if not abs_url_regex.search(href):
                    new_href = re.sub(r'rss/index\.html$', 'rss/index.rss', href)
                    new_href = re.sub(r'/index\.html$', '/', new_href)
                    e.attr('href', new_href)
                    print("\t", href, "=>", new_href)
            if parser == 'html':
                return d.html(method='html')#.encode('utf8')
            return d.__unicode__()#.encode('utf8')

        # fix links in all html files
        for root, dirs, filenames in os.walk(static_path):
            for filename in filenames:
              if filename.endswith(('.html', '.xml', '.xls')):
                filepath = os.path.join(root, filename)
                if filename.endswith(('.html')):
                  parser = 'html'
                elif filename.endswith(('.xml', '.xls')):
                  parser = 'xml'
                if root.endswith("/rss"):  # rename rss index.html to index.rss
                    parser = 'xml'
                    newfilepath = os.path.join(root, os.path.splitext(filename)[0] + ".rss")
                    os.rename(filepath, newfilepath)
                    filepath = newfilepath
                with open(filepath, encoding='utf8') as f:
                    filetext = f.read()
                print ("Fixing links in ", filepath)
                newtext = fixLinks(filetext, parser)
                with open(filepath, 'w', encoding='utf8', errors="surrogateescape") as f:
                    f.write(newtext)

        def grabAndConvert(matchobj):
          match = matchobj.group(0)

          # Split off the portion after the first /, check if it exists
          filePath = match.split(arguments['--domain'], 1)[-1]

          if(len(filePath) > 1):
            #print("Path at " + filePath)
            if (not filePath.endswith("/") and (not path.exists(static_path+"/" + filePath))):
              print("[WARNING] " + filePath + " was not downloaded by wget earlier")
              # If not, wget it
              getFile(filePath)
              getFile(filePath + ".map") # Check if there's a map object

          # After, return the fixed URL
          fixedURL = re.sub(r"%s" % arguments['--domain'], arguments['--new-domain'], match)

          return fixedURL

        def grabAndConvertHREF(matchobj):
          match = matchobj.group(0)

          # Split off the portion after the first /, check if it exists
          filePath = match.split("href=\"", 1)[-1]

          if filePath.startswith("/") and not arguments['--domain'] in match:
            if(len(filePath) > 1):
              #print("Path at " + filePath)
              if (not filePath.endswith("/") and (not path.exists(static_path+"/" + filePath))):
                print("[WARNING] " + filePath + " was not downloaded by wget earlier")
                # If not, wget it
                getFile(filePath)
                getFile(filePath + ".map") # Check if there's a map object

            return "href=\"" + arguments['--domain'] + filePath

          return match

        def grabAndConvertSRC(matchobj):
          match = matchobj.group(0)

          # Split off the portion after the first /, check if it exists
          filePath = match.split("src=\"", 1)[-1]

          if filePath.startswith("/") and not filePath.startswith("//") and not arguments['--domain'] in match:
            if(len(filePath) > 1):
              #print("Path at " + filePath)
              if (not filePath.endswith("/") and (not path.exists(static_path+"/" + filePath))):
                print("[WARNING] " + filePath + " was not downloaded by wget earlier")
                # If not, wget it
                getFile(filePath)
                getFile(filePath + ".map") # Check if there's a map object

            return "src=\"" + arguments['--domain'] + filePath

          return match

        # fix all localhost references, if new domain given
        if arguments['--new-domain']:
            filetypes = ['*.html', '*.xml', '*.xsl', '*.rss', 'robots.txt']
            for root, dirs, filenames in os.walk(static_path):
                for extension in filetypes:
                    for filename in fnmatch.filter(filenames, extension):
                        filepath = os.path.join(root, filename)
                        with open(filepath, encoding='utf8') as f:
                            filetext = f.read()
                            print("Fixing localhost references in ", filepath)

                            # Check if the file this path represents exists, and if not, wget it
                            newtext = re.sub((r"%s" % "href=\"") + r"[^\'|\"|\<|\>|\?]*", grabAndConvertHREF, filetext)
                            newtext = re.sub((r"%s" % "src=\"" ) + r"[^\'|\"|\<|\>|\?]*", grabAndConvertSRC ,  newtext)
                            newtext = re.sub((r"%s" % arguments['--domain']) + r"[^\'|\"|\<|\>|\?]*", grabAndConvert, newtext)
                            #newtext = re.sub((r"%s" % "/assets/built") + r"[^\'|\"|\<|\>|\?]*", grabAndConvert, newtext)
                            #newtext = re.sub(r"%s" % "\"/assets/built/", "\""+ arguments['--new-domain'] + "/assets/built/", newtext)
                            #newtext = re.sub(r"%s" % "/favicon.ico", arguments['--new-domain'] + "/favicon.ico", newtext)
                            newtext = re.sub(r"%s" % arguments['--domain'], arguments['--new-domain'], newtext) # Cleanup anything I miss
                        with open(filepath, 'w', encoding='utf-8-sig') as f:
                            f.write(newtext)

    elif arguments['preview']:
        os.chdir(static_path)

        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", 9000), Handler)

        print ("Serving at port 9000")
        # gracefully handle interrupt here
        httpd.serve_forever()

    else:
        print (__doc__)

if __name__ == '__main__':
    main()
