from django.db import models

class BibRecord(models.Model):
	mmsid = models.CharField(max_length=15)
	language_code = models.CharField(max_length=3)
	place_code = models.CharField(max_length=3)
	material_type = models.CharField(max_length=20)
	resource_type = models.CharField(max_length=50)

	class Meta:
		indexes = [
			models.Index(fields=['mmsid']),
			models.Index(fields=['language_code']),
			models.Index(fields=['place_code']),
		]


class Field962(models.Model):
	# Subfields can be repeatable (R) or non-repeatable (NR).
	# Repeatable subfields are stored as 'val1, val2...' which is OK for this purpose.
	bib_record = models.ForeignKey(BibRecord, on_delete=models.CASCADE)
	cat_center = models.CharField(max_length=20)	# $a (NR)
	cataloger = models.CharField(max_length=20)		# $b (NR)
	yyyymm = models.CharField(max_length=6)			# $c (NR)
	difficulty = models.CharField(max_length=20)	# $d (NR)
	maint_info = models.CharField(max_length=20)	# $g (NR)
	# Moved to RepeatableSubfield
	# national_info = models.CharField(max_length=20)	# $h (R)
	# naco_info = models.CharField(max_length=20)		# $i (R)
	# saco_info = models.CharField(max_length=20)		# $j (R)
	# project = models.CharField(max_length=20)		# $k (R)

	class Meta:
		indexes = [
			models.Index(fields=['cat_center']),
			models.Index(fields=['cataloger']),
			models.Index(fields=['yyyymm']),
		]

class RepeatableSubfield(models.Model):
	field_962 = models.ForeignKey(Field962, on_delete=models.CASCADE)
	# for repeatable 962 $h, $i, $j, $k
	subfield_code = models.CharField(max_length=1)
	subfield_value = models.CharField(max_length=20)

	class Meta:
		indexes = [
			models.Index(fields=['subfield_code']),
			models.Index(fields=['subfield_value']),
		]
