function focus_first_input() {
  $('input[type=text]')[0].focus();
}

function submit() {
  var i, inputs = $('input');
  for (i = 0 ; i < inputs.length ; ++i) {
    if (inputs[i].value.length < 1) {
      alert('All values are required!');
      focus_first_input();
      return
    }
  }
  $('form')[0].submit();
  focus_first_input();
}

$(document).ready(focus_first_input);

