from dataclasses import dataclass

@dataclass
class TitleInfo:
	is_movie: bool
	disk: str
	disk_name: str # CINFO:2,0
	title_name: str # TINFO:\d,27
	title: int # TINFO
	length: str # TINFO:\d,9
	size: str   # TINFO:\d,10
	v_resolution: int # SINFO:\d,\d,19
	final_name: str = ''
	show: str = ''
	season: str = ''

	def preset(self, is_high_quality) -> str:
		encode_res = 720 if self.v_resolution>=720 else 480
		if is_high_quality:
			return f'HQ {encode_res}p30 Surround'
		else:
			return f'Fast {encode_res}p30'