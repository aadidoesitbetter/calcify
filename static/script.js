document.addEventListener('DOMContentLoaded', () => {
    const displayCurrent = document.getElementById('current-display');
    const displayHistory = document.getElementById('history-display');
    const keypad = document.getElementById('keypad');
    const modeSelector = document.getElementById('mode-selector');
    const converterControls = document.getElementById('converter-controls');
    const sciKeypad = document.getElementById('sci-keypad');

    // Converter Elements
    const convType = document.getElementById('conv-type');
    const unitFrom = document.getElementById('unit-from');
    const unitTo = document.getElementById('unit-to');

    let currentInput = '0';
    let previousInput = '';
    let operator = null;
    let mode = 'standard';
    let currencyRates = {};

    // --- Mode Switching ---
    modeSelector.addEventListener('change', (e) => {
        mode = e.target.value;
        setMode(mode);
    });

    function setMode(newMode) {
        mode = newMode;
        // Reset inputs
        currentInput = '0';
        previousInput = '';
        operator = null;
        updateDisplay();

        // Visibility Toggles
        sciKeypad.classList.add('hidden');
        converterControls.classList.add('hidden');

        if (mode === 'scientific') {
            sciKeypad.classList.remove('hidden');
        } else if (mode === 'converter') {
            converterControls.classList.remove('hidden');
            loadConverterOptions();
        }
    }

    // --- Button Event Listeners ---
    function attachListeners() {
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const val = btn.dataset.val;
                handleInput(action, val);
            });
        });
    }

    // --- Input Handling ---
    function handleInput(action, val) {
        if (mode === 'converter') {
            handleConverterInput(action, val);
            return;
        }

        if (action === 'number') {
            if (currentInput === '0' && val !== '.') currentInput = val;
            else if (val === '.' && currentInput.includes('.')) return;
            else currentInput += val;
        } else if (action === 'operator') {
            if (previousInput && operator) calculate();
            previousInput = currentInput;
            currentInput = '0';
            operator = val;
        } else if (action === 'calculate') {
            calculate();
        } else if (action === 'clear') {
            currentInput = '0';
            previousInput = '';
            operator = null;
        } else if (action === 'backspace') {
            currentInput = currentInput.slice(0, -1) || '0';
        } else if (action === 'sci') {
            handleSciFunc(val);
        } else if (action === 'brackets') {
            // simplified bracket logic
            if (val === '()') currentInput += '()';
            else currentInput += val;
        } else if (action === 'percent') {
            currentInput = String(parseFloat(currentInput) / 100);
        }

        updateDisplay();
    }

    function handleSciFunc(func) {
        if (func === 'pi') {
            currentInput = String(Math.PI);
        } else if (func === 'e') {
            currentInput = String(Math.E);
        } else if (['(', ')'].includes(func)) {
            if (currentInput === '0') currentInput = func;
            else currentInput += func;
        } else {
            // Math functions
            let val = parseFloat(currentInput);
            if (func === 'sin') currentInput = String(Math.sin(val));
            else if (func === 'cos') currentInput = String(Math.cos(val));
            else if (func === 'tan') currentInput = String(Math.tan(val));
            else if (func === 'log') currentInput = String(Math.log10(val));
            else if (func === 'ln') currentInput = String(Math.log(val));
            else if (func === 'sqrt') currentInput = String(Math.sqrt(val));
        }
    }

    function calculate() {
        if (!previousInput || !operator) return;

        let prev = parseFloat(previousInput);
        let curr = parseFloat(currentInput);
        let result = 0;

        if (operator === '+') result = prev + curr;
        else if (operator === '-') result = prev - curr;
        else if (operator === '*') result = prev * curr;
        else if (operator === '/') result = prev / curr;
        else if (operator === '**') result = Math.pow(prev, curr);
        else if (operator === 'yroot') result = Math.pow(prev, 1 / curr);

        currentInput = String(result);
        previousInput = '';
        operator = null;
    }

    function updateDisplay() {
        displayCurrent.textContent = currentInput;
        displayHistory.textContent = (previousInput + (operator ? ' ' + operator : ''));
    }

    // --- Converter Logic ---
    function loadConverterOptions() {
        convType.addEventListener('change', updateUnits);
        updateUnits();
    }

    const units = {
        'length': ['m', 'km', 'ft', 'mi', 'cm', 'inch'],
        'weight': ['kg', 'g', 'lb', 'oz'],
        'currency': ['USD', 'EUR', 'GBP', 'JPY', 'INR']
    };

    function updateUnits() {
        const type = convType.value;
        const options = units[type] || [];

        // Populate standard units
        if (type === 'currency' && Object.keys(currencyRates).length > 0) {
            populateSelect(unitFrom, Object.keys(currencyRates));
            populateSelect(unitTo, Object.keys(currencyRates));
        } else {
            populateSelect(unitFrom, options);
            populateSelect(unitTo, options);
        }

        // Fetch currency if needed
        if (type === 'currency') fetchCurrency();
    }

    function populateSelect(select, opts) {
        select.innerHTML = '';
        opts.forEach(o => {
            const opt = document.createElement('option');
            opt.value = o;
            opt.textContent = o;
            select.appendChild(opt);
        });
        if (opts.length > 1 && select === unitTo) select.selectedIndex = 1;
    }

    async function fetchCurrency() {
        if (Object.keys(currencyRates).length > 0) return;
        try {
            const res = await fetch('/api/currency');
            const data = await res.json();
            if (data.rates) {
                currencyRates = data.rates;
                updateUnits();
            }
        } catch (e) {
            console.error("Currency fetch failed", e);
        }
    }

    function handleConverterInput(action, val) {
        if (action === 'number') {
            if (currentInput === '0' && val !== '.') currentInput = val;
            else if (val === '.' && currentInput.includes('.')) return;
            else currentInput += val;
        } else if (action === 'clear') {
            currentInput = '0';
        } else if (action === 'backspace') {
            currentInput = currentInput.slice(0, -1) || '0';
        }

        displayCurrent.textContent = currentInput;
        convert();
    }

    function convert() {
        const type = convType.value;
        const from = unitFrom.value;
        const to = unitTo.value;
        const val = parseFloat(currentInput);
        let result = 0;

        if (isNaN(val)) return;

        if (type === 'length') {
            const toM = { "m": 1, "km": 1000, "ft": 0.3048, "mi": 1609.34, "cm": 0.01, "inch": 0.0254 };
            const valM = val * toM[from];
            result = valM / toM[to];
        } else if (type === 'weight') {
            const toKg = { "kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495 };
            const valKg = val * toKg[from];
            result = valKg / toKg[to];
        } else if (type === 'currency' && currencyRates[from]) {
            const rateFrom = currencyRates[from];
            const rateTo = currencyRates[to];
            const valUsd = val / rateFrom;
            result = valUsd * rateTo;
        }

        displayHistory.textContent = `= ${result.toFixed(4)} ${to}`;
    }

    unitFrom.addEventListener('change', convert);
    unitTo.addEventListener('change', convert);

    // Init
    attachListeners();
    setMode('standard');
});
