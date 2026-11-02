# Door animation completion / cleanup — narrow FFDec evidence

Original game.swf SHA256: 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9.
Source: Java 8 + repository FFDec export in successful SWF Original Audit GitHub Actions run 40998902161, artifact original-flash-audit (ID 12952870432).

All five original frame scripts have identical content: stop(); _root.Open_room = 2; SHA256 d7f9a7754b689755b4637277b2a6ed45d643ebd4d8a142beeedbf2741900f57a.

| Original ActionScript path | Frame |
| --- | ---: |
| export/scripts/DefineSprite_171_mt_15/frame_5/DoAction.as | 5 |
| export/scripts/DefineSprite_205_mt_05/frame_10/DoAction.as | 10 |
| export/scripts/DefineSprite_213_mt_03/frame_10/DoAction.as | 10 |
| export/scripts/DefineSprite_209_mt_04/frame_10/DoAction.as | 10 |
| export/scripts/DefineSprite_217_mt_02/frame_10/DoAction.as | 10 |

export/scripts/DefineSprite_855/frame_1/DoAction.as SHA256 3c6de7a67bd0e02e57438ec13cbcd081f1a5487a981e1bb960f2e0872bdddb38:
~~~actionscript
if(_root.Open_room == 2)
{
   temp_name = "_root.mt_m_" add _root.Last_x add "_" add _root.Last_y;
   _root.DelMovie(temp_name);
   _root.Open_room = 0;
   _root.Now_key_flag = 1;
}
~~~

frame_4346/DoAction_2.as SHA256 0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034 starts supported doors with Now_key_flag=0, Open_room=1, removes map tile, and saves Last_x/Last_y.

The new Python and JavaScript probes model ONLY these explicit events. The caller must observe the actual sprite and frame; no invented frame timing or rendering is performed. Cleanup uses saved original coordinates and resets Open_room=0 / Now_key_flag=1. Regression tests compose the existing arrow router with these transitions for three ordinary doors, and separately verify mt_05 frame 10 and mt_15 frame 5.

These are synthetic deterministic vectors, NOT captured original gameplay. The remove_map_sprite effect is descriptive, not actual rendering. No complete Pygame/HTML5 UI, door sound duration, other sprite855 branches, ending or 1:1 signoff is claimed. Gymnasium/Kaggle remains locked.
