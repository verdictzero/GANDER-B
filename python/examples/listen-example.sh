#!/bin/bash
# Example usage of the TEDF Message Listener

echo "TEDF Message Listener Examples"
echo "=============================="
echo ""

echo "1. Basic listening (pretty mode):"
echo "   python3 tedf-listener.py"
echo ""

echo "2. Compact mode (one line per message):"
echo "   python3 tedf-listener.py -m compact"
echo ""

echo "3. Raw JSON output:"
echo "   python3 tedf-listener.py -m raw"
echo ""

echo "4. Filter for only position updates:"
echo "   python3 tedf-listener.py -f compact -m compact"
echo ""

echo "5. Stats only mode:"
echo "   python3 tedf-listener.py -m stats"
echo ""

echo "6. Connect to remote simulator:"
echo "   python3 tedf-listener.py -a tcp://192.168.1.100 -p 5555"
echo ""

echo "7. Save raw output to file:"
echo "   python3 tedf-listener.py -m raw > tedf_messages.json"
echo ""

echo "Starting basic listener in 3 seconds..."
sleep 3

# Start the listener with pretty mode
python3 ../tedf-listener.py -m pretty