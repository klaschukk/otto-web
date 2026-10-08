// Масштаб превью: iframe рисует страницу шириной 390px и ужимается под ширину карточки
function fit(){document.querySelectorAll('.ex-frame').forEach(f=>f.style.setProperty('--s',f.clientWidth/390))}
addEventListener('resize',fit);fit();
