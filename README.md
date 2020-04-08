# fo4Terminal
Heuristic for solving terminals in Fallout 4

example: https://gfycat.com/dishonestdarlingfowl

If you want to do this manually, just create a set of the words on the terminal then call `suggest_click(words)` until the terminal is opened

`suggest_click` works by going through each word in the set and finding how many words would be left in the terminal if the word's likeness to the actual answer was `x`. `x` cycles from 0 to the length of the word, and the average of all of the words left with all `x` is that word's score. The word with the lowest score is the suggested click, and is printed next to the word.
