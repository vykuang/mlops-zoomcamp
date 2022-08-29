# Data Wrangling

Pipeline `|` operator is the crux of data wrangling. To wrangle, you need

1. data to wrangle
2. something to do with it

Do what? usually `grep` and then `>` to direct the STDOUT into a file, or `less` to page the output for viewing on terminal.

## `sed`

sed is a *stream editor*, built on top of old `ed`. Common usage is to search and replace:

```bash
# ssh log to my GCP compute instance
ssh gcp-mlops journalctl
	| grep sshd # only ssh related log
	| grep "Disconnected from" 
	| sed 's/.*Disconnected from//'
```

Returns all ssh related log and replaced the distracting "Disconnected from" with nothing. The `.*` means any one character, matched 0+ times; i.e. everything before "Disconnected".

General pattern is `s/REGEX/SUBSTITUION/`, similar to Vim's same feature.

### Regex

Common regex *special* characters, at least in `sed` context:

- `.` any single char, except newline
- `*` 0+ preceding match
- `+` 1+ preceding match
- `[abc]` any one of a, b, and c
- `[0-9]` any one of 1, 2, ..., 9
- `(RX1|RX2)` matches either RX1 or RX2 pattern
- `^` start of line
- `$` end of line

In `sed`, surround regex with `/` to use these special characters, or pass `-E`

So our above query can return all user activites, but what if a user is literally named "Disconnected from"? Our wrangling would completely erase that name, leaving an unknown user activity in our log. Normally we would have:

```bash
Jan 17 03:13:00 thesquareplanet.com sshd[2631]: Disconnected from invalid user Disconnected from 46.97.239.16 port 55920 [preauth]
```

After our naive regex we'd have:

```bash
46.97.239.16 port 55920 [preauth]
```

Regex can also help us catch this.

1. Make our "Disconnected From" non-greedy by adding "?": `s/.*?Disconnected From//'`; note that this is available only in `perl` mode, via `perl -pe`
2. We match the entire line:

```bash
 | sed -E 's/.*Disconnected from (invalid |authenticating )?user (.*) [^ ]+ port [0-9]+( \[preauth\])?$/\2/'
``` 

* `.*Disconnected from ` starts same as before
* `(invalid |authenticating ) ?user ` matches "invalid user" or "authenticating user"
* `(.*) [^ ]+ ` matches usernames; the second portion specifically matches any non-empty seq of non-space chars
* until we get to `port [0-9]+( \[preauth\])?$`, which matches port [port number], and then optionally [preauth] and finally end of string, with `$`.

Now instead of replacing with nothing, we'd like to replace it with the user name we matched. How do we do that?

Any string matched by regex in parentheses is captured, and can be referenced via `\1`,`\2`, etc. depending on which group captured the string. For us it would be the second (first is invalid/auth) 

## `sort | uniq -c`

First sort our results, and then combine duplicates with `uniq -C`, C for combining duplicates.

We could pipe *again* to `sort -nk1,1` which *sorts numerically by the 1st whitespace-separated column, until the 1st field*

Combine with `head` or `tail` to get the least or most common counts.

## `awk`

What if we now want to compile this list of users into a comma-separated list, say for a config file?

We'd pipe the `tail` output to:

```bash
| awk '{print $2}' | paste -sd,
```

paste lets us combine lines (`-s`) by a single char delimiter (`d`, specified as `,`)

But what is `awk`? It is another prog language for handling text streams. 

What `{print $2}` does is it matches all *lines*, and prints the 2nd field of that line. But why? awk takes the form of an optional pattern, plus a block saying what to do when the pattern matches a line. `$2` matches the 2nd field; fields are by default separated by spaces, modified via `-F`. 

Example that counts number of single-use usernames that start with `c` and end with `e`:

```bash
 | awk '$1 == 1 && $2 ~ /^c[^ ]*e$/ { print $2 }' | wc -l
```

Recall that we've sort'd and uniq'd the `journalctl` output and so `$1` corresponds to the count, and `$2` to username.

* count must == 1, *and*
* Username must start with `c`, have any number of non-space characters, then at the end of string, `e` must be present.
* print all results that match
* `wc -l` counts the lines

## R and gnuplot

so we can also pipe the output from `awk` into `R` to use their data analysis tools. Or just `gnuplot` if we want plotting. 

* `| awk '{print $1}' | R --no-echo -e 'x <- scan(file="stdin", quiet=TRUE); summary(x)'`
* `| tail -n10
 | gnuplot -p -e 'set boxwidth 0.5; plot "-" using 1:xtic(2) with boxes'`

## `xargs`

After wrangling, the "cleaned" output can be converted from STDIN to function arguments with `xarg` for other commands 
