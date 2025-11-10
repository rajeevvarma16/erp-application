document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
  
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
  
    // Replace these with your actual validation rules
    const validUsername = 'user';
    const validPassword = 'password123';
  
    if (username === validUsername && password === validPassword) {
      alert('Login successful!');
    } else {
      document.getElementById('error-message').style.display = 'block';
    }
  });
  