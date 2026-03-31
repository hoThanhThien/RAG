# ✅ Test Thread Management Features

## 🎯 Tính năng đã thêm

### Backend APIs:
1. **GET /support/threads/my/all** - Lấy danh sách tất cả threads của user
2. **POST /support/threads/new** - Tạo thread mới
3. **DELETE /support/threads/{id}** - Xóa thread

### Frontend Features:
1. **Thread List Sidebar** - Hiển thị danh sách các cuộc trò chuyện
2. **Create New Thread Button** - Tạo cuộc trò chuyện mới
3. **Delete Thread Button** - Xóa cuộc trò chuyện
4. **Switch Thread** - Chuyển đổi giữa các cuộc trò chuyện

## 🧪 Test Cases

### Test 1: Xem danh sách threads
```bash
# Request
GET http://localhost:8000/support/threads/my/all
Authorization: Bearer <user_token>

# Expected Response
[
  {
    "thread_id": 1,
    "created_at": "2025-11-11T10:00:00",
    "last_content": "Xin chào",
    "last_time": "2025-11-11T10:05:00",
    "message_count": 5
  }
]
```

### Test 2: Tạo thread mới
```bash
# Request
POST http://localhost:8000/support/threads/new
Authorization: Bearer <user_token>

# Expected Response
{
  "thread_id": 2,
  "message": "Đã tạo cuộc trò chuyện mới"
}
```

### Test 3: Xóa thread
```bash
# Request
DELETE http://localhost:8000/support/threads/1
Authorization: Bearer <user_token>

# Expected Response
{
  "message": "Đã xóa cuộc trò chuyện thành công"
}

# Test case: Không thể xóa thread của người khác
# Expected: 403 Forbidden
```

## 🎨 UI Components

### Thread List Sidebar
- **Trigger**: Click vào icon menu (☰) ở góc trái header
- **Display**: 
  - Danh sách threads với preview tin nhắn cuối
  - Số lượng tin nhắn
  - Thời gian cập nhật
  - Button xóa mỗi thread
  - Button "Tạo mới" ở đầu
- **Interactions**:
  - Click thread → Chuyển sang thread đó
  - Click "Tạo mới" → Tạo thread mới và chuyển sang nó
  - Click icon xóa → Confirm và xóa thread

### Visual Design
- Active thread: Background gradient tím nhạt
- Hover effect: Slide sang phải một chút
- Smooth animations: slideInLeft (0.3s)
- Responsive: Full width trên mobile

## 📋 User Flow

### Flow 1: Tạo cuộc trò chuyện mới
1. User mở chat widget
2. Click icon menu (☰)
3. Click button "Tạo mới"
4. Hệ thống tạo thread mới
5. Chat box reset với thread mới
6. Thread list refresh hiển thị thread mới

### Flow 2: Chuyển đổi giữa các cuộc trò chuyện
1. User mở thread list
2. Click vào thread khác
3. Hệ thống load messages của thread đó
4. Chat box hiển thị messages mới
5. Thread list đóng lại

### Flow 3: Xóa cuộc trò chuyện
1. User mở thread list
2. Click icon xóa ở thread muốn xóa
3. Confirm dialog hiện ra
4. User confirm
5. Hệ thống xóa thread
6. Nếu đang xem thread bị xóa → Chuyển sang thread khác hoặc tạo mới
7. Thread list refresh

## 🔧 Technical Details

### State Management
```javascript
const [showThreadList, setShowThreadList] = useState(false);
const [threads, setThreads] = useState([]);
const [threadId, setThreadId] = useState(null);
```

### Key Functions
- `loadThreads()` - Load danh sách threads
- `createNewThread()` - Tạo thread mới
- `deleteThread(threadId)` - Xóa thread
- `switchThread(threadId)` - Chuyển thread

### WebSocket Behavior
- Khi switch thread → Disconnect và reconnect với thread mới
- Messages real-time chỉ cho thread đang active

## 🎯 Testing Checklist

### Backend
- [x] API trả về đúng threads của user
- [x] Không thể xem threads của user khác
- [x] Tạo thread mới thành công
- [x] Xóa thread cascade (xóa cả messages)
- [x] Không thể xóa thread của người khác

### Frontend
- [ ] Thread list hiển thị đúng
- [ ] Click menu icon toggle thread list
- [ ] Button "Tạo mới" hoạt động
- [ ] Switch thread load đúng messages
- [ ] Delete thread có confirm dialog
- [ ] Active thread highlight đúng
- [ ] Animations smooth
- [ ] Responsive trên mobile

### Integration
- [ ] WebSocket reconnect khi switch thread
- [ ] Messages real-time cho thread đúng
- [ ] Sau khi xóa thread đang xem, auto switch
- [ ] Thread list auto refresh sau create/delete

## 🚀 Deployment Steps

1. **Backend**: Restart server để load endpoints mới
2. **Frontend**: Reload page để load code mới
3. **Test**: Mở chat widget và test các tính năng
4. **Verify**: Check console logs và network requests

## 💡 Improvements Planned

- [ ] Search threads
- [ ] Filter threads (unread, by date)
- [ ] Thread titles (custom names)
- [ ] Archive threads (thay vì xóa hẳn)
- [ ] Pin important threads
- [ ] Unread message count badge
- [ ] Keyboard shortcuts (Ctrl+N new thread)
