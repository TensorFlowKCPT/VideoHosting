const username = document.getElementById('username');
const passwordInput = document.getElementById('passwordInput');
const passwordRepeat = document.getElementById('passwordRepeat');
const nickname = document.getElementById('nickname');

let usernameFlag = false;
let passwordInputFlag = false;
let passwordRepeatFlag = false;
let nicknameFlag = false;

username.addEventListener('input', function() {
    const usernameValue = username.value;
    usernameFlag = usernameValue.length > 0;
    updateValidationStyles();
});

passwordInput.addEventListener('input', function() {
    const passwordInputValue = passwordInput.value;
    const passwordPattern = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_]).{8,}$/;
    passwordInputFlag = passwordPattern.test(passwordInputValue);
    updateValidationStyles();
});

passwordRepeat.addEventListener('input', function() {
    const passwordRepeatValue = passwordRepeat.value;
    passwordRepeatFlag = passwordRepeatValue === passwordInput.value;
    updateValidationStyles();
});

nickname.addEventListener('input', function() {
    const nicknameValue = nickname.value;
    nicknameFlag = nicknameValue.length > 0;
    updateValidationStyles();
});

function updateValidationStyles() {
    username.style.boxShadow = usernameFlag ? '0 0 10px green' : '0 0 10px red';
    passwordInput.style.boxShadow = passwordInputFlag ? '0 0 10px green' : '0 0 10px red';
    passwordRepeat.style.boxShadow = passwordRepeatFlag ? '0 0 10px green' : '0 0 10px red';
    nickname.style.boxShadow = nicknameFlag ? '0 0 10px green' : '0 0 10px red';

    const checkPasswordButton = document.getElementById('checkPassword');
    checkPasswordButton.disabled = !(usernameFlag && passwordInputFlag && passwordRepeatFlag && nicknameFlag);
}