# Right-to-left subtitles

Some or most video players do not render right-to-left text well.  Though right-to-left letters come out in the corect order, punctuation at the end of the line gets shifted to the start of the line. 

Instead of marking the text as right-to-left,  which would be the clean solution but not necessarily supported by video players, the usual
solution is to move punctuation from the end of the line to the start. 
This open-source project does that.  The video players will render the text to look like a correct sentence with punctuation  at the end.



#Usage

Compose your SRT file normally, then call this tool as follows:
`subtitles-righttoleft.py file_in [file_out]`

If not given, the output file is the same as the input file but with `rtl_` prepended.