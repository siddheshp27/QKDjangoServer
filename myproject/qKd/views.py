# myapi/views.py

from rest_framework import status
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from qiskit import QuantumCircuit, transpile, assemble
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import random
import base64


KEY_LENGTH = 100

def random_bit():
    return random.choice([0, 1])

def random_basis():
    return random.choice(['+', 'x'])

def prepare_qubit(bit, basis):
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if basis == 'x':
        qc.h(0)
    return qc

def measure_qubit(qc, basis):
    if basis == 'x':
        qc.h(0)
    qc.measure(0, 0)
    return qc

def generate_bases(length):
    return [random_basis() for _ in range(length)]

def generate_key_and_bases(length):
    key = [random_bit() for _ in range(length)]
    bases = generate_bases(length)
    return key, bases

def sift_keys(sender_key, sender_bases, receiver_bases):
    sifted_key = []
    sifted_indices = []
    for i in range(len(sender_key)):
        if sender_bases[i] == receiver_bases[i]:
            sifted_key.append(sender_key[i])
            sifted_indices.append(i)
    return sifted_key, sifted_indices

def estimate_error_rate(sifted_key_sender, sifted_key_receiver):
    mismatches = sum(1 for s, r in zip(sifted_key_sender, sifted_key_receiver) if s != r)
    error_rate = mismatches / len(sifted_key_sender)
    return error_rate

def error_correction(sifted_key_sender, sifted_key_receiver):
    corrected_key = []
    for s, r in zip(sifted_key_sender, sifted_key_receiver):
        if s == r:
            corrected_key.append(s)
    return corrected_key

def quantumKeyGenerator():
    simulator = Aer.get_backend('qasm_simulator')

    # Step 1: Sender generates key and bases
    sender_key, sender_bases = generate_key_and_bases(KEY_LENGTH)
    print(f"Sender Key: {sender_key}")
    print(f"Sender Bases: {sender_bases}")

    # Step 2: Receiver generates random bases
    receiver_bases = generate_bases(KEY_LENGTH)
    print(f"Receiver Bases: {receiver_bases}")

    receiver_measurements = []

    for i in range(KEY_LENGTH):
        # Sender prepares the qubit
        qc = prepare_qubit(sender_key[i], sender_bases[i])
        
        # Receiver measures the qubit
        qc = measure_qubit(qc, receiver_bases[i])
        
        # Execute the circuit on the qasm simulator
        compiled_circuit = transpile(qc, simulator)
        qobj = assemble(compiled_circuit)
        result = simulator.run(qobj).result()
        counts = result.get_counts(qc)
        
        # Record the measurement result
        measurement = max(counts, key=counts.get)  # Get the most probable result
        receiver_measurements.append(int(measurement))

    print(f"Receiver Measurements: {receiver_measurements}")

    # Step 3: Sift the keys
    sifted_key_sender, sifted_indices = sift_keys(sender_key, sender_bases, receiver_bases)
    sifted_key_receiver = [receiver_measurements[i] for i in sifted_indices]

    print(f"Sifted Key (Sender): {sifted_key_sender}")
    print(f"Sifted Key (Receiver): {sifted_key_receiver}")

    # Step 4: Estimate the error rate
    error_rate = estimate_error_rate(sifted_key_sender, sifted_key_receiver)
    print(f"Error Rate: {error_rate * 100:.2f}%")

    # Assuming no eavesdropper, continue with the next steps regardless of the error rate
    # Step 5: Error Correction
    corrected_key = error_correction(sifted_key_sender, sifted_key_receiver)
    print(f"Corrected Key: {corrected_key}")

    # The final corrected key is now ready for use
    final_key = corrected_key
    final_key_string = ""
    for char in final_key:
        final_key_string += str(char)  
    print(f"Final Key: {final_key_string}")
    return final_key_string

def pad_key(key, length):
    if len(key) >= length:
        return key[:length]
    else:
        return key.ljust(length, '0')


@api_view(['GET'])
def createQuantumKeys(request):
    keystrarr = []
    for i in range(10):
        key = quantumKeyGenerator()
        padded_key = pad_key(key, 256)
        base64_key = base64.b64encode(padded_key.encode()).decode()
        keystrarr.append(base64_key)
    print(keystrarr)
    return JsonResponse(keystrarr, safe=False)

