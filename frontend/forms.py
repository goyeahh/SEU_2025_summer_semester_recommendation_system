from django import forms

class RatingForm(forms.Form):
    # 创建一个从1到10的选项
    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="为这部电影打分"
    )