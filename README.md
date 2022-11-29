# ass_bundle
Bundle AutoDesk Arnolds .ass files to be portable.

```                                                                                                
 Usage: python -m ass_bundle run [OPTIONS] SOURCE TARGET                                           
                                                                                                   
 Run via commandline.                                                                              
                                                                                                   
╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────╮
│ *    source      PATH  Source directory of the ass files. [default: None] [required]            │
│ *    target      PATH  Target directory for all resources. [default: None] [required]           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────╮
│ --dry-run          Don't write any files.                                                       │
│ --help             Show this message and exit.                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────╯

```