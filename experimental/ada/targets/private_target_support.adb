with Top_Targets;

--  Each forbidden client access has an independent legal control.
procedure Private_Target_Support is
   type Host is new Top_Targets.Target with null record;
   Object : Host;
#if not TokenAccess then
   Handle : Top_Targets.Identity_Handle;
#end if;
begin
#if TokenAccess then
#if Illegal then
   pragma Assert (Object.Token.State /= null);
#else
   pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Object)));
#end if;
#else
   Handle := Top_Targets.Identity (Object);
#if Illegal then
   Top_Targets.Finalize (Handle);
#else
   pragma Assert (Top_Targets.Is_Live (Handle));
#end if;
#end if;
end Private_Target_Support;
