# Vim

[Source notes](https://missing.csail.mit.edu/2020/editors/)

## Intro

### Philosophy

In programming, most time is spent reading/editing, not writing. Thus, Vim employs *modal* editing. It has different modes for inserting and manipulating and viewing text. It is *programmable* via vimscript or even python. The interface itself is somehow a programming language. Vim avoids using the mouse.

### Modal editing

* normal (ESC) - moving through file and editing
* insert (i) - default mode in other word processors
* replace (R) - replacing
* visual (plain: `v`, line: `V`, block: `ctrl-V`) - selecting blocks
* command-line (`:`) - to run commands

Return to normal mode via `ESC`; consider remapping CapsLock to ESC due to the frequent use of ESC.

## Basics

### Insert

Press `i` to go from normal mode to insert mode. This is what people are familiar with but is not the most efficient way to use vim

### buffers, tabs, windos

Vim can have a number of open files, or *buffers*, in each session. Each session in turn can have multiple tabs, and in those tabs, could have several buffers open in their own window.

This is in contrast to web browsers where each tab is its own buffer. In Vim, each tab can have multiple buffers. 

In addition, those buffers need not be different files, but different view of the same file, kind of like split view in excel

Defaults to single tab with single window.

### command-line

Accessed via `:` from normal mode. Enables saving, opening, closing, exitting.

* `:q` quit, `:q!` to quit without saving
* `:w` write, or save
* `:e {name_of_file}` open file for edit
* `:ls` show open buffers
* `:help {topic}` info on things like `:w` or `w` for what those keys do

## Interface as a programming language

Keystrokes are commands, and commands *compose*.

### Movement

Most time should be in `normal` mode. Use these movement commands to navigate the buffer, instead of scrolling and using mouse:

* basic: `hkjl` - left down up right
* words: `w` next word, `b` beginning of word, `e` end of word
* lines: `0` beginning of line, `^` first non-blank char, `$` end of line
* screen: `H` top, `M` middle, `L` bottom
* scroll: `ctrl-u` up, `ctrl-d` down
* file: `gg` beginning, `G` end
* line num: `:{num}<CR>` teleport to that line
* Find: `f/t/F/T{char}` to find or *to* forward/backward the character on current line
	* `,`, `;` to navigate matches
* search: `/{regex}`, `n`/`N` to nav matches`

### selection

Use the same movement keys above, but in `visual` mode, to make selections. Press `v` to enter visual mode, `V` for visual line, `ctrl-v` for visual block

### Edit

* Insert mode, but manipulating/deleting should be done in other modes.
* `o`/`O` to insert line above/below
* `d{motion}` to delete:
	* `w` to delete word
	* `$` to end of line
	* `0` to beginning of line
	* `l` char
* `c{motion}` to change:
	* `w` word
	* `cw` will delete the word and then enter Insert mode
* `x` delete char immediately after cursor
* `s` subs char, equiv to `x`, `i`
* also works in visual mode: d to delete, c to change selection
* `u` undo, `Ctrl-r` redo
* `y` copy, or *yank*, `p` paste
* `A` to append to end of line

### Modifying commands with numbers

Combine nouns/verbs with count, to repeat the action

* `3w` move 3 words forward
* `4j` move down 4 lines
* `7dw` delete 7 words

### Modifiers

Adding `i` or `a` modifies verb behaviour to inner, or around

* `ci(` change contents inside current pair of `()`
* `ci[` change inside current pair of `[]`
* `da'` deletes the single quoted str located by cursor, as well as the surrounding single quote. 
* badf (edited) [replaced sq bracket]

### Broken fizz buzz

Fixed:

```python
#!/usr/bin/env python
import sys
def fizz_buzz(limit):
    for i in range(1, limit+1):
        if i % 3 == 0 and i % 5 == 0:
            print('fizzbuzz')


        elif i % 3 == 0:
            print('fizz')
        elif i % 5 == 0:
            print('buzz')
        else:
            print(i)

def main(num):
    fizz_buzz(num)

if __name__ == '__main__':
        main(int(sys.argv[1]))def fizz_buzz(limit):
    for i in range(1, limit):
        if i % 3 == 0:
            print('fizz')
        if i % 5 == 0:
            print('buzz')
        if i % 3 and i % 5:
            print('fizzbuzz')

def main(num):
    fizz_buzz(num)

if __name__ == '__main__':
	main(int(sys.argv[1]))
```

### Customizing vim

Use `~/.vimrc` as config file to customize the interface, e.g. using Capslock instead of Esc to return to normal mode

### Plugin

The `ctrlP` plugin enables fuzzy file finder via the `:CtrlP` command within vim.

Installation and docs here: [Github for ctrlP](https://github.com/ctrlpvim/ctrlp.vim)

Instead of using `:CtrlP`, can configure within `vimrc` to use `Ctrl+P` instead of vim command line to activate file finder

## Resources
## Exercises

Complete `vimtutor` (which comes with vim installation) by running it in shell


