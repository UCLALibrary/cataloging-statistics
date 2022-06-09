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
	bib_record = models.ForeignKey(BibRecord, on_delete=models.CASCADE)
	cat_center = models.CharField(max_length=20)	# $a
	cataloger = models.CharField(max_length=20)		# $b
	yyyymm = models.CharField(max_length=6)			# $c
	difficulty = models.CharField(max_length=20)	# $d
	maint_info = models.CharField(max_length=20)	# $g
	national_info = models.CharField(max_length=20)	# $h
	naco_info = models.CharField(max_length=20)		# $i
	saco_info = models.CharField(max_length=20)		# $j
	project = models.CharField(max_length=20)		# $k

	class Meta:
		indexes = [
			models.Index(fields=['cat_center']),
			models.Index(fields=['cataloger']),
			models.Index(fields=['yyyymm']),
		]