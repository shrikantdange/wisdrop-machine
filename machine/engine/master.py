"""Two-pass loudnorm master to -14 LUFS / -1.5 dBTP (single pass overshot to -1.0 dBTP). usage: python master.py in.wav out.wav"""
import sys, json, subprocess
i, o = sys.argv[1], sys.argv[2]
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', i, '-af', 'loudnorm=I=-14:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = (f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,alimiter=limit=0.84:attack=1:release=50:level=false")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', i, '-af', af, '-ar', '48000', o], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', o, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1]); print('master', m['input_i'], 'LUFS', m['input_tp'], 'dBTP')
