<?php
// Đường dẫn đến file script JSX
$photoshopScript = 'C:\\Program Files\\Adobe\\Adobe Photoshop 2025\\Presets\\Scripts\\outline_cursor_ps.jsx';

// Đường dẫn đến file input và output
$inputFile = 'D:\\#Cyrus\\py_render\\img\\sample.png';
$outputFilePS = 'D:\\#Cyrus\\py_render\\img\\sample_test.ps';
$outputFileEPS = 'D:\\#Cyrus\\py_render\\img\\sample_test.eps';

// Kiểm tra hệ điều hành và tạo lệnh tương ứng để gọi script
if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
    // Windows
    $commandPS = "cscript //nologo \"$photoshopScript\" \"$inputFile\" \"$outputFilePS\"";
    $commandEPS = "cscript //nologo \"$photoshopScript\" \"$inputFile\" \"$outputFileEPS\"";
} else {
    // macOS
    $commandPS = "osascript -e 'tell application \"Adobe Photoshop\" to do javascript file \"$photoshopScript\" with arguments {\"$inputFile\", \"$outputFilePS\"}'";
    $commandEPS = "osascript -e 'tell application \"Adobe Photoshop\" to do javascript file \"$photoshopScript\" with arguments {\"$inputFile\", \"$outputFileEPS\"}'";
}

// Thực thi lệnh cho PostScript
exec($commandPS, $outputPS, $return_varPS);
if ($return_varPS === 0) {
    echo "PNG to PS conversion executed successfully.\n";
} else {
    echo "PNG to PS conversion execution failed.\n";
}

// Thực thi lệnh cho EPS
exec($commandEPS, $outputEPS, $return_varEPS);
if ($return_varEPS === 0) {
    echo "PNG to EPS conversion executed successfully.\n";
} else {
    echo "PNG to EPS conversion execution failed.\n";
}
