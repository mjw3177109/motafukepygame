if(left_hp > 0 || right_hp > 0)
{
   if(kill_number % 2 == 0)
   {
      kill_max = random(200);
      if(kill_max <= _root.Now_life)
      {
         left_hp -= kill_right * 2;
         _root.PlaySound("music_08");
      }
      else
      {
         left_hp -= kill_right;
         _root.PlaySound("music_05");
      }
      if(left_hp < 0)
      {
         left_hp = 0;
      }
   }
   if(kill_number % 2 == 1)
   {
      right_hp -= kill_left;
      if(left_gong > right_fang)
      {
         _root.PlaySound("music_12");
      }
      else
      {
         _root.PlaySound("music_13");
      }
      if(left_hp == 0)
      {
         gotoAndPlay(35);
      }
   }
   kill_number++;
}
