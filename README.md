# minesweepyr-ai
My personal project to make an efficient minesweeper solving AI, with screen interaction for actually playing it in browser/etc. The AI itself is designed to be relatively independent of any actual game program, so it can be easily adapted to different programs. Personally, I test it on minesweeper.online's game.

In essence, the AI takes a "raw grid" of the tiles from the screen/etc, and gives tiles that needs to be clicked, marked, and "found out", i.e. tiles that the AI needs to know what they changed to. (e.x. if you click an unknown tile, the AI will need to know what was under that unknown.) The AI does its best to keep its own state "in the background", & the iteration process repeats until the AI either messes up somewhere or can't find anything else to do.
