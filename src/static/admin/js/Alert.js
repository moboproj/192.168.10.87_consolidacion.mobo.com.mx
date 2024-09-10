function errorajax(error) {
    Swal.fire({
        icon: "error",
        title: "Oops...",
        text: "Error: " + error  // Mostrar el mensaje de error recibido
    });
}
     function Loading(){
        let timerInterval;
        Swal.fire({
            title: "Cargando datos!",
            html: "Esta pantalla se cerrara en :<b></b> milisegundos.",
            timer: 5500,
            timerProgressBar: true,
            allowOutsideClick: false,
            allowEscapeKey: false,
            allowEnterKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
                const timer = Swal.getPopup().querySelector("b");
                timerInterval = setInterval(() => {
                    timer.textContent = `${Swal.getTimerLeft()}`;
                }, 100);
            },
            willClose: () => {
                clearInterval(timerInterval);
            }
        }).then((result) => {
            if (result.dismiss === Swal.DismissReason.timer) {
                console.log("I was closed by the timer");
            }
        });
    }

 