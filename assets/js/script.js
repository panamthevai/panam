function copyCommand() {
    var cmd = "curl -sL https://panamthevai.github.io/panam | bash";
    navigator.clipboard.writeText(cmd).then(function() {
        alert("🚀 கட்டளை காப்பி செய்யப்பட்டது! அதை அப்படியே Termux-இல் பேஸ்ட் செய்யவும்.");
    }, function() {
        alert("❌ காப்பி செய்ய முடியவில்லை!");
    });
}
