# Generated by Django 4.0.1 on 2022-06-15 01:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BibRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mmsid', models.CharField(max_length=20)),
                ('language_code', models.CharField(max_length=3)),
                ('place_code', models.CharField(max_length=3)),
                ('material_type', models.CharField(max_length=20)),
                ('resource_type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Field962',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat_center', models.CharField(max_length=20)),
                ('cataloger', models.CharField(max_length=20)),
                ('yyyymm', models.CharField(max_length=6)),
                ('difficulty', models.CharField(max_length=20)),
                ('maint_info', models.CharField(max_length=20)),
                ('bib_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catstats.bibrecord')),
            ],
        ),
        migrations.CreateModel(
            name='RepeatableSubfield',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subfield_code', models.CharField(max_length=1)),
                ('subfield_value', models.CharField(max_length=50)),
                ('field_962', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catstats.field962')),
            ],
        ),
        migrations.AddIndex(
            model_name='bibrecord',
            index=models.Index(fields=['mmsid'], name='catstats_bi_mmsid_bc0d4d_idx'),
        ),
        migrations.AddIndex(
            model_name='bibrecord',
            index=models.Index(fields=['language_code'], name='catstats_bi_languag_c15682_idx'),
        ),
        migrations.AddIndex(
            model_name='bibrecord',
            index=models.Index(fields=['place_code'], name='catstats_bi_place_c_66a03d_idx'),
        ),
        migrations.AddIndex(
            model_name='repeatablesubfield',
            index=models.Index(fields=['subfield_code'], name='catstats_re_subfiel_facb9d_idx'),
        ),
        migrations.AddIndex(
            model_name='repeatablesubfield',
            index=models.Index(fields=['subfield_value'], name='catstats_re_subfiel_2e025f_idx'),
        ),
        migrations.AddIndex(
            model_name='field962',
            index=models.Index(fields=['cat_center'], name='catstats_fi_cat_cen_74c4e3_idx'),
        ),
        migrations.AddIndex(
            model_name='field962',
            index=models.Index(fields=['cataloger'], name='catstats_fi_catalog_ebac9e_idx'),
        ),
        migrations.AddIndex(
            model_name='field962',
            index=models.Index(fields=['yyyymm'], name='catstats_fi_yyyymm_aa593c_idx'),
        ),
    ]
