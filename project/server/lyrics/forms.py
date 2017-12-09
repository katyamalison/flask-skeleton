from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class TryAgainForm(FlaskForm):
    artist1 = StringField(
        'First artist',
        validators=[
            DataRequired(),
            Length(min=1, max=40)
        ]
    )

    artist2 = StringField(
        'Second artist',
        validators=[
            DataRequired(),
            Length(min=1, max=40)
        ]
    ) 
    
class InputArtistForm(FlaskForm):
    artist1 = StringField(
        'First artist',
        validators=[
            DataRequired(),
            Length(min=1, max=40)
        ]
    )

    artist2 = StringField(
        'Second artist',
        validators=[
            DataRequired(),
            Length(min=1, max=40)
        ]
    ) 
