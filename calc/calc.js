/* Operations */
const calculate = {
    '+': (a, b) => a + b,
    '-': (a, b) => (+a && +b) ? a - b : (+a ? -a : -b),
    '*': (a, b) => a * b,
    '/': (a, b) => a / b,
    '%': (a, b) => a % b,
    '^': (a, b) => Math.pow(a, b),
};

/* Immediately calculate square root in place */
function parseRoot(str) {

    let search = /sqrt\((\-?\d+)\)/;
    let sqrt = (m) => Math.sqrt(parseFloat(m.substr(5, m.length-6)));

    return str.replace(search, sqrt);

}

/* Calculate the string */
function calc(str) {

    let search = /(\+|\-|\*|\/|\%|\^)/;
    let parts = parseRoot(str).split(search).map((x) => x.trim()).filter((x) => x !== '');
    let total = 0;
    
    for (let i=0; i<parts.length; i++) {

        if (parts[i] in calculate) {

            if (['-', '+'].includes(parts[i+1])) {
                parts[i+1] = parts[i+1] + parts.splice(i+2, 1)[0];
            }

            let operate = calculate[parts[i]];
            let next = +parts[++i];

            total = operate(total, next);

        } else {

            total = +parts[i];

        }

    }

    return total;

}

/* Calculate the rest */
function recalculate() {

    let input = document.getElementById('query');
    let output = document.getElementById('result');
    let calculated = calc(input.value);
    let errormsg = "Invalid input";
    output.innerHTML = isNaN(calculated) ? errormsg : calculated;

}
