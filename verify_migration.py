from employees.models import JobTitle
from accounts.models import User

print('📊 JobTitle records:', JobTitle.objects.count())
for jt in JobTitle.objects.all():
    print('  -', jt.title)

print()
print('👥 Users with job titles:', User.objects.exclude(job_title__isnull=True).count())
print('✅ Migration verification complete!')