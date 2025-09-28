"""
Grammar-to-Extension Mapping

Maps Atom editor grammar identifiers to file extensions for syntax highlighting.
Atom allows users to select grammar per note for improved readability
and syntax highlighting.

NOTE: Some grammars (like `Gemfile`, `gitconfig`) are typically extensionless in their
ecosystems. The CLI exports these with their grammar name as the extension
(e.g., `ruby-deps__000.Gemfile`) to maintain the filename pattern and prevent
collisions between multiple notes using the same grammar.
"""

GRAMMAR_TO_EXTENSION = {
    "source.c": "c",
    "source.cake": "cake",
    "source.clojure": "clj",
    "source.coffee": "coffee",
    "source.cpp": "cpp",
    "source.cs": "cs",
    "source.css": "css",
    "source.css.less": "less",
    "source.css.scss": "scss",
    "source.csx": "csx",
    "source.flow": "js",
    "source.gfm": "md",
    "source.git-config": "gitconfig",
    "source.go": "go",
    "source.java": "java",
    "source.java-properties": "properties",
    "source.js": "js",
    "source.js.rails source.js.jquery": "js",
    "source.json": "json",
    "source.litcoffee": "litcoffee",
    "source.makefile": "mk",
    "source.mod": "mod",
    "source.objc": "m",
    "source.objcpp": "mm",
    "source.perl": "pl",
    "source.perl6": "pl6",
    "source.plist": "plist",
    "source.python": "py",
    "source.regexp.python": "re",
    "source.ruby": "rb",
    "source.ruby.gemfile": "Gemfile",
    "source.ruby.rails": "rb",
    "source.ruby.rails.rjs": "rjs",
    "source.rust": "rs",
    "source.sass": "sass",
    "source.shell": "sh",
    "source.sql": "sql",
    "source.sql.ruby": "erbsql",
    "source.strings": "strings",
    "source.toml": "toml",
    "source.ts": "ts",
    "source.tsx": "tsx",
    "source.yaml": "yaml",
    "text.git-commit": "txt",
    "text.git-rebase": "txt",
    "text.html.basic": "html",
    "text.html.ejs": "ejs",
    "text.html.erb": "erb",
    "text.html.gohtml": "gohtml",
    "text.html.jsp": "jsp",
    "text.html.mustache": "mustache",
    "text.html.php": "php",
    "text.html.ruby": "erb",
    "text.plain": "txt",
    "text.plain.null-grammar": "txt",
    "text.null-grammar": "txt",
    "null-grammar": "txt",
    "text.python.console": "py",
    "text.python.traceback": "pytb",
    "text.shell-session": "sh",
    "text.xml": "xml",
    "text.xml.plist": "plist",
    "text.xml.xsl": "xsl",
}
