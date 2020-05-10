#Todofetcher
## If you're using vim...
If you're using vim, then there's a good way to not have to close the file while running these programs are making changes to the file. In your `.vimrc`, make sure the following lines are somewhere in there.

```
set autoread
set updatetime=750
au CursorHold * checktime
```

