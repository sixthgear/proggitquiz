from django import forms
from pq.models import Problem, Solution, Bonus, Set
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

CONTENT_TYPES = ['text', 'application']
MAX_UPLOAD_SIZE = 102400 # 2.5MB - 2621440

class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ['output_user', 'source']

    def clean(self):
        cleaned_data = super(SolutionForm, self).clean()
        output_gen = self.instance.output_gen
        output_user = cleaned_data.get('output_user')
        source = cleaned_data.get('source')

        if not output_user:
            raise forms.ValidationError('No output provided.')

        if not source:
            raise forms.ValidationError('No source code provided.')            

        for f in [output_user, source]:
            content_type = f.content_type.split('/')[0]
            if content_type in CONTENT_TYPES:
                print f._size
                if int(f._size) > MAX_UPLOAD_SIZE:
                    raise forms.ValidationError('Filesize exceeds %s.' % filesizeformat(MAX_UPLOAD_SIZE))
            else:            
                raise forms.ValidationError('File type is not supported!')
            
        for i,(a,b) in enumerate(map(None, output_user, output_gen.splitlines())):
            a = a.strip() if a else ''
            b = b.strip() if b else ''
            if a != b:                
                raise forms.ValidationError('Your output failed on line %d!' % (i+1))
                # raise forms.ValidationError('Your output was incorrect.')

        return cleaned_data