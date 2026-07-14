var Vo = { exports: {} }, Nr = {}, Uo = { exports: {} }, Q = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ha;
function cf() {
  if (Ha) return Q;
  Ha = 1;
  var u = Symbol.for("react.element"), a = Symbol.for("react.portal"), c = Symbol.for("react.fragment"), y = Symbol.for("react.strict_mode"), w = Symbol.for("react.profiler"), x = Symbol.for("react.provider"), T = Symbol.for("react.context"), L = Symbol.for("react.forward_ref"), z = Symbol.for("react.suspense"), k = Symbol.for("react.memo"), H = Symbol.for("react.lazy"), B = Symbol.iterator;
  function J(h) {
    return h === null || typeof h != "object" ? null : (h = B && h[B] || h["@@iterator"], typeof h == "function" ? h : null);
  }
  var le = { isMounted: function() {
    return !1;
  }, enqueueForceUpdate: function() {
  }, enqueueReplaceState: function() {
  }, enqueueSetState: function() {
  } }, ve = Object.assign, K = {};
  function X(h, S, Z) {
    this.props = h, this.context = S, this.refs = K, this.updater = Z || le;
  }
  X.prototype.isReactComponent = {}, X.prototype.setState = function(h, S) {
    if (typeof h != "object" && typeof h != "function" && h != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
    this.updater.enqueueSetState(this, h, S, "setState");
  }, X.prototype.forceUpdate = function(h) {
    this.updater.enqueueForceUpdate(this, h, "forceUpdate");
  };
  function ie() {
  }
  ie.prototype = X.prototype;
  function Ee(h, S, Z) {
    this.props = h, this.context = S, this.refs = K, this.updater = Z || le;
  }
  var pe = Ee.prototype = new ie();
  pe.constructor = Ee, ve(pe, X.prototype), pe.isPureReactComponent = !0;
  var ge = Array.isArray, Pe = Object.prototype.hasOwnProperty, we = { current: null }, G = { key: !0, ref: !0, __self: !0, __source: !0 };
  function oe(h, S, Z) {
    var Y, $ = {}, ee = null, se = null;
    if (S != null) for (Y in S.ref !== void 0 && (se = S.ref), S.key !== void 0 && (ee = "" + S.key), S) Pe.call(S, Y) && !G.hasOwnProperty(Y) && ($[Y] = S[Y]);
    var te = arguments.length - 2;
    if (te === 1) $.children = Z;
    else if (1 < te) {
      for (var he = Array(te), nn = 0; nn < te; nn++) he[nn] = arguments[nn + 2];
      $.children = he;
    }
    if (h && h.defaultProps) for (Y in te = h.defaultProps, te) $[Y] === void 0 && ($[Y] = te[Y]);
    return { $$typeof: u, type: h, key: ee, ref: se, props: $, _owner: we.current };
  }
  function Xe(h, S) {
    return { $$typeof: u, type: h.type, key: S, ref: h.ref, props: h.props, _owner: h._owner };
  }
  function Fe(h) {
    return typeof h == "object" && h !== null && h.$$typeof === u;
  }
  function Ve(h) {
    var S = { "=": "=0", ":": "=2" };
    return "$" + h.replace(/[=:]/g, function(Z) {
      return S[Z];
    });
  }
  var V = /\/+/g;
  function b(h, S) {
    return typeof h == "object" && h !== null && h.key != null ? Ve("" + h.key) : S.toString(36);
  }
  function Ce(h, S, Z, Y, $) {
    var ee = typeof h;
    (ee === "undefined" || ee === "boolean") && (h = null);
    var se = !1;
    if (h === null) se = !0;
    else switch (ee) {
      case "string":
      case "number":
        se = !0;
        break;
      case "object":
        switch (h.$$typeof) {
          case u:
          case a:
            se = !0;
        }
    }
    if (se) return se = h, $ = $(se), h = Y === "" ? "." + b(se, 0) : Y, ge($) ? (Z = "", h != null && (Z = h.replace(V, "$&/") + "/"), Ce($, S, Z, "", function(nn) {
      return nn;
    })) : $ != null && (Fe($) && ($ = Xe($, Z + (!$.key || se && se.key === $.key ? "" : ("" + $.key).replace(V, "$&/") + "/") + h)), S.push($)), 1;
    if (se = 0, Y = Y === "" ? "." : Y + ":", ge(h)) for (var te = 0; te < h.length; te++) {
      ee = h[te];
      var he = Y + b(ee, te);
      se += Ce(ee, S, Z, he, $);
    }
    else if (he = J(h), typeof he == "function") for (h = he.call(h), te = 0; !(ee = h.next()).done; ) ee = ee.value, he = Y + b(ee, te++), se += Ce(ee, S, Z, he, $);
    else if (ee === "object") throw S = String(h), Error("Objects are not valid as a React child (found: " + (S === "[object Object]" ? "object with keys {" + Object.keys(h).join(", ") + "}" : S) + "). If you meant to render a collection of children, use an array instead.");
    return se;
  }
  function Ue(h, S, Z) {
    if (h == null) return h;
    var Y = [], $ = 0;
    return Ce(h, Y, "", "", function(ee) {
      return S.call(Z, ee, $++);
    }), Y;
  }
  function Me(h) {
    if (h._status === -1) {
      var S = h._result;
      S = S(), S.then(function(Z) {
        (h._status === 0 || h._status === -1) && (h._status = 1, h._result = Z);
      }, function(Z) {
        (h._status === 0 || h._status === -1) && (h._status = 2, h._result = Z);
      }), h._status === -1 && (h._status = 0, h._result = S);
    }
    if (h._status === 1) return h._result.default;
    throw h._result;
  }
  var ae = { current: null }, O = { transition: null }, P = { ReactCurrentDispatcher: ae, ReactCurrentBatchConfig: O, ReactCurrentOwner: we };
  function R() {
    throw Error("act(...) is not supported in production builds of React.");
  }
  return Q.Children = { map: Ue, forEach: function(h, S, Z) {
    Ue(h, function() {
      S.apply(this, arguments);
    }, Z);
  }, count: function(h) {
    var S = 0;
    return Ue(h, function() {
      S++;
    }), S;
  }, toArray: function(h) {
    return Ue(h, function(S) {
      return S;
    }) || [];
  }, only: function(h) {
    if (!Fe(h)) throw Error("React.Children.only expected to receive a single React element child.");
    return h;
  } }, Q.Component = X, Q.Fragment = c, Q.Profiler = w, Q.PureComponent = Ee, Q.StrictMode = y, Q.Suspense = z, Q.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = P, Q.act = R, Q.cloneElement = function(h, S, Z) {
    if (h == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + h + ".");
    var Y = ve({}, h.props), $ = h.key, ee = h.ref, se = h._owner;
    if (S != null) {
      if (S.ref !== void 0 && (ee = S.ref, se = we.current), S.key !== void 0 && ($ = "" + S.key), h.type && h.type.defaultProps) var te = h.type.defaultProps;
      for (he in S) Pe.call(S, he) && !G.hasOwnProperty(he) && (Y[he] = S[he] === void 0 && te !== void 0 ? te[he] : S[he]);
    }
    var he = arguments.length - 2;
    if (he === 1) Y.children = Z;
    else if (1 < he) {
      te = Array(he);
      for (var nn = 0; nn < he; nn++) te[nn] = arguments[nn + 2];
      Y.children = te;
    }
    return { $$typeof: u, type: h.type, key: $, ref: ee, props: Y, _owner: se };
  }, Q.createContext = function(h) {
    return h = { $$typeof: T, _currentValue: h, _currentValue2: h, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, h.Provider = { $$typeof: x, _context: h }, h.Consumer = h;
  }, Q.createElement = oe, Q.createFactory = function(h) {
    var S = oe.bind(null, h);
    return S.type = h, S;
  }, Q.createRef = function() {
    return { current: null };
  }, Q.forwardRef = function(h) {
    return { $$typeof: L, render: h };
  }, Q.isValidElement = Fe, Q.lazy = function(h) {
    return { $$typeof: H, _payload: { _status: -1, _result: h }, _init: Me };
  }, Q.memo = function(h, S) {
    return { $$typeof: k, type: h, compare: S === void 0 ? null : S };
  }, Q.startTransition = function(h) {
    var S = O.transition;
    O.transition = {};
    try {
      h();
    } finally {
      O.transition = S;
    }
  }, Q.unstable_act = R, Q.useCallback = function(h, S) {
    return ae.current.useCallback(h, S);
  }, Q.useContext = function(h) {
    return ae.current.useContext(h);
  }, Q.useDebugValue = function() {
  }, Q.useDeferredValue = function(h) {
    return ae.current.useDeferredValue(h);
  }, Q.useEffect = function(h, S) {
    return ae.current.useEffect(h, S);
  }, Q.useId = function() {
    return ae.current.useId();
  }, Q.useImperativeHandle = function(h, S, Z) {
    return ae.current.useImperativeHandle(h, S, Z);
  }, Q.useInsertionEffect = function(h, S) {
    return ae.current.useInsertionEffect(h, S);
  }, Q.useLayoutEffect = function(h, S) {
    return ae.current.useLayoutEffect(h, S);
  }, Q.useMemo = function(h, S) {
    return ae.current.useMemo(h, S);
  }, Q.useReducer = function(h, S, Z) {
    return ae.current.useReducer(h, S, Z);
  }, Q.useRef = function(h) {
    return ae.current.useRef(h);
  }, Q.useState = function(h) {
    return ae.current.useState(h);
  }, Q.useSyncExternalStore = function(h, S, Z) {
    return ae.current.useSyncExternalStore(h, S, Z);
  }, Q.useTransition = function() {
    return ae.current.useTransition();
  }, Q.version = "18.3.1", Q;
}
var Aa;
function Xo() {
  return Aa || (Aa = 1, Uo.exports = cf()), Uo.exports;
}
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ba;
function df() {
  if (Ba) return Nr;
  Ba = 1;
  var u = Xo(), a = Symbol.for("react.element"), c = Symbol.for("react.fragment"), y = Object.prototype.hasOwnProperty, w = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, x = { key: !0, ref: !0, __self: !0, __source: !0 };
  function T(L, z, k) {
    var H, B = {}, J = null, le = null;
    k !== void 0 && (J = "" + k), z.key !== void 0 && (J = "" + z.key), z.ref !== void 0 && (le = z.ref);
    for (H in z) y.call(z, H) && !x.hasOwnProperty(H) && (B[H] = z[H]);
    if (L && L.defaultProps) for (H in z = L.defaultProps, z) B[H] === void 0 && (B[H] = z[H]);
    return { $$typeof: a, type: L, key: J, ref: le, props: B, _owner: w.current };
  }
  return Nr.Fragment = c, Nr.jsx = T, Nr.jsxs = T, Nr;
}
var Xa;
function ff() {
  return Xa || (Xa = 1, Vo.exports = df()), Vo.exports;
}
var o = ff(), fe = Xo(), Vl = {}, qo = { exports: {} }, $e = {}, Ho = { exports: {} }, Ao = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Za;
function pf() {
  return Za || (Za = 1, (function(u) {
    function a(O, P) {
      var R = O.length;
      O.push(P);
      e: for (; 0 < R; ) {
        var h = R - 1 >>> 1, S = O[h];
        if (0 < w(S, P)) O[h] = P, O[R] = S, R = h;
        else break e;
      }
    }
    function c(O) {
      return O.length === 0 ? null : O[0];
    }
    function y(O) {
      if (O.length === 0) return null;
      var P = O[0], R = O.pop();
      if (R !== P) {
        O[0] = R;
        e: for (var h = 0, S = O.length, Z = S >>> 1; h < Z; ) {
          var Y = 2 * (h + 1) - 1, $ = O[Y], ee = Y + 1, se = O[ee];
          if (0 > w($, R)) ee < S && 0 > w(se, $) ? (O[h] = se, O[ee] = R, h = ee) : (O[h] = $, O[Y] = R, h = Y);
          else if (ee < S && 0 > w(se, R)) O[h] = se, O[ee] = R, h = ee;
          else break e;
        }
      }
      return P;
    }
    function w(O, P) {
      var R = O.sortIndex - P.sortIndex;
      return R !== 0 ? R : O.id - P.id;
    }
    if (typeof performance == "object" && typeof performance.now == "function") {
      var x = performance;
      u.unstable_now = function() {
        return x.now();
      };
    } else {
      var T = Date, L = T.now();
      u.unstable_now = function() {
        return T.now() - L;
      };
    }
    var z = [], k = [], H = 1, B = null, J = 3, le = !1, ve = !1, K = !1, X = typeof setTimeout == "function" ? setTimeout : null, ie = typeof clearTimeout == "function" ? clearTimeout : null, Ee = typeof setImmediate < "u" ? setImmediate : null;
    typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
    function pe(O) {
      for (var P = c(k); P !== null; ) {
        if (P.callback === null) y(k);
        else if (P.startTime <= O) y(k), P.sortIndex = P.expirationTime, a(z, P);
        else break;
        P = c(k);
      }
    }
    function ge(O) {
      if (K = !1, pe(O), !ve) if (c(z) !== null) ve = !0, Me(Pe);
      else {
        var P = c(k);
        P !== null && ae(ge, P.startTime - O);
      }
    }
    function Pe(O, P) {
      ve = !1, K && (K = !1, ie(oe), oe = -1), le = !0;
      var R = J;
      try {
        for (pe(P), B = c(z); B !== null && (!(B.expirationTime > P) || O && !Ve()); ) {
          var h = B.callback;
          if (typeof h == "function") {
            B.callback = null, J = B.priorityLevel;
            var S = h(B.expirationTime <= P);
            P = u.unstable_now(), typeof S == "function" ? B.callback = S : B === c(z) && y(z), pe(P);
          } else y(z);
          B = c(z);
        }
        if (B !== null) var Z = !0;
        else {
          var Y = c(k);
          Y !== null && ae(ge, Y.startTime - P), Z = !1;
        }
        return Z;
      } finally {
        B = null, J = R, le = !1;
      }
    }
    var we = !1, G = null, oe = -1, Xe = 5, Fe = -1;
    function Ve() {
      return !(u.unstable_now() - Fe < Xe);
    }
    function V() {
      if (G !== null) {
        var O = u.unstable_now();
        Fe = O;
        var P = !0;
        try {
          P = G(!0, O);
        } finally {
          P ? b() : (we = !1, G = null);
        }
      } else we = !1;
    }
    var b;
    if (typeof Ee == "function") b = function() {
      Ee(V);
    };
    else if (typeof MessageChannel < "u") {
      var Ce = new MessageChannel(), Ue = Ce.port2;
      Ce.port1.onmessage = V, b = function() {
        Ue.postMessage(null);
      };
    } else b = function() {
      X(V, 0);
    };
    function Me(O) {
      G = O, we || (we = !0, b());
    }
    function ae(O, P) {
      oe = X(function() {
        O(u.unstable_now());
      }, P);
    }
    u.unstable_IdlePriority = 5, u.unstable_ImmediatePriority = 1, u.unstable_LowPriority = 4, u.unstable_NormalPriority = 3, u.unstable_Profiling = null, u.unstable_UserBlockingPriority = 2, u.unstable_cancelCallback = function(O) {
      O.callback = null;
    }, u.unstable_continueExecution = function() {
      ve || le || (ve = !0, Me(Pe));
    }, u.unstable_forceFrameRate = function(O) {
      0 > O || 125 < O ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : Xe = 0 < O ? Math.floor(1e3 / O) : 5;
    }, u.unstable_getCurrentPriorityLevel = function() {
      return J;
    }, u.unstable_getFirstCallbackNode = function() {
      return c(z);
    }, u.unstable_next = function(O) {
      switch (J) {
        case 1:
        case 2:
        case 3:
          var P = 3;
          break;
        default:
          P = J;
      }
      var R = J;
      J = P;
      try {
        return O();
      } finally {
        J = R;
      }
    }, u.unstable_pauseExecution = function() {
    }, u.unstable_requestPaint = function() {
    }, u.unstable_runWithPriority = function(O, P) {
      switch (O) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          O = 3;
      }
      var R = J;
      J = O;
      try {
        return P();
      } finally {
        J = R;
      }
    }, u.unstable_scheduleCallback = function(O, P, R) {
      var h = u.unstable_now();
      switch (typeof R == "object" && R !== null ? (R = R.delay, R = typeof R == "number" && 0 < R ? h + R : h) : R = h, O) {
        case 1:
          var S = -1;
          break;
        case 2:
          S = 250;
          break;
        case 5:
          S = 1073741823;
          break;
        case 4:
          S = 1e4;
          break;
        default:
          S = 5e3;
      }
      return S = R + S, O = { id: H++, callback: P, priorityLevel: O, startTime: R, expirationTime: S, sortIndex: -1 }, R > h ? (O.sortIndex = R, a(k, O), c(z) === null && O === c(k) && (K ? (ie(oe), oe = -1) : K = !0, ae(ge, R - h))) : (O.sortIndex = S, a(z, O), ve || le || (ve = !0, Me(Pe))), O;
    }, u.unstable_shouldYield = Ve, u.unstable_wrapCallback = function(O) {
      var P = J;
      return function() {
        var R = J;
        J = P;
        try {
          return O.apply(this, arguments);
        } finally {
          J = R;
        }
      };
    };
  })(Ao)), Ao;
}
var Ja;
function hf() {
  return Ja || (Ja = 1, Ho.exports = pf()), Ho.exports;
}
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ka;
function mf() {
  if (Ka) return $e;
  Ka = 1;
  var u = Xo(), a = hf();
  function c(e) {
    for (var n = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, t = 1; t < arguments.length; t++) n += "&args[]=" + encodeURIComponent(arguments[t]);
    return "Minified React error #" + e + "; visit " + n + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  var y = /* @__PURE__ */ new Set(), w = {};
  function x(e, n) {
    T(e, n), T(e + "Capture", n);
  }
  function T(e, n) {
    for (w[e] = n, e = 0; e < n.length; e++) y.add(n[e]);
  }
  var L = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), z = Object.prototype.hasOwnProperty, k = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, H = {}, B = {};
  function J(e) {
    return z.call(B, e) ? !0 : z.call(H, e) ? !1 : k.test(e) ? B[e] = !0 : (H[e] = !0, !1);
  }
  function le(e, n, t, r) {
    if (t !== null && t.type === 0) return !1;
    switch (typeof n) {
      case "function":
      case "symbol":
        return !0;
      case "boolean":
        return r ? !1 : t !== null ? !t.acceptsBooleans : (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-");
      default:
        return !1;
    }
  }
  function ve(e, n, t, r) {
    if (n === null || typeof n > "u" || le(e, n, t, r)) return !0;
    if (r) return !1;
    if (t !== null) switch (t.type) {
      case 3:
        return !n;
      case 4:
        return n === !1;
      case 5:
        return isNaN(n);
      case 6:
        return isNaN(n) || 1 > n;
    }
    return !1;
  }
  function K(e, n, t, r, l, i, s) {
    this.acceptsBooleans = n === 2 || n === 3 || n === 4, this.attributeName = r, this.attributeNamespace = l, this.mustUseProperty = t, this.propertyName = e, this.type = n, this.sanitizeURL = i, this.removeEmptyString = s;
  }
  var X = {};
  "children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
    X[e] = new K(e, 0, !1, e, null, !1, !1);
  }), [["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(e) {
    var n = e[0];
    X[n] = new K(n, 1, !1, e[1], null, !1, !1);
  }), ["contentEditable", "draggable", "spellCheck", "value"].forEach(function(e) {
    X[e] = new K(e, 2, !1, e.toLowerCase(), null, !1, !1);
  }), ["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(e) {
    X[e] = new K(e, 2, !1, e, null, !1, !1);
  }), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
    X[e] = new K(e, 3, !1, e.toLowerCase(), null, !1, !1);
  }), ["checked", "multiple", "muted", "selected"].forEach(function(e) {
    X[e] = new K(e, 3, !0, e, null, !1, !1);
  }), ["capture", "download"].forEach(function(e) {
    X[e] = new K(e, 4, !1, e, null, !1, !1);
  }), ["cols", "rows", "size", "span"].forEach(function(e) {
    X[e] = new K(e, 6, !1, e, null, !1, !1);
  }), ["rowSpan", "start"].forEach(function(e) {
    X[e] = new K(e, 5, !1, e.toLowerCase(), null, !1, !1);
  });
  var ie = /[\-:]([a-z])/g;
  function Ee(e) {
    return e[1].toUpperCase();
  }
  "accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
    var n = e.replace(
      ie,
      Ee
    );
    X[n] = new K(n, 1, !1, e, null, !1, !1);
  }), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
    var n = e.replace(ie, Ee);
    X[n] = new K(n, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
  }), ["xml:base", "xml:lang", "xml:space"].forEach(function(e) {
    var n = e.replace(ie, Ee);
    X[n] = new K(n, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
  }), ["tabIndex", "crossOrigin"].forEach(function(e) {
    X[e] = new K(e, 1, !1, e.toLowerCase(), null, !1, !1);
  }), X.xlinkHref = new K("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), ["src", "href", "action", "formAction"].forEach(function(e) {
    X[e] = new K(e, 1, !1, e.toLowerCase(), null, !0, !0);
  });
  function pe(e, n, t, r) {
    var l = X.hasOwnProperty(n) ? X[n] : null;
    (l !== null ? l.type !== 0 : r || !(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (ve(n, t, l, r) && (t = null), r || l === null ? J(n) && (t === null ? e.removeAttribute(n) : e.setAttribute(n, "" + t)) : l.mustUseProperty ? e[l.propertyName] = t === null ? l.type === 3 ? !1 : "" : t : (n = l.attributeName, r = l.attributeNamespace, t === null ? e.removeAttribute(n) : (l = l.type, t = l === 3 || l === 4 && t === !0 ? "" : "" + t, r ? e.setAttributeNS(r, n, t) : e.setAttribute(n, t))));
  }
  var ge = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, Pe = Symbol.for("react.element"), we = Symbol.for("react.portal"), G = Symbol.for("react.fragment"), oe = Symbol.for("react.strict_mode"), Xe = Symbol.for("react.profiler"), Fe = Symbol.for("react.provider"), Ve = Symbol.for("react.context"), V = Symbol.for("react.forward_ref"), b = Symbol.for("react.suspense"), Ce = Symbol.for("react.suspense_list"), Ue = Symbol.for("react.memo"), Me = Symbol.for("react.lazy"), ae = Symbol.for("react.offscreen"), O = Symbol.iterator;
  function P(e) {
    return e === null || typeof e != "object" ? null : (e = O && e[O] || e["@@iterator"], typeof e == "function" ? e : null);
  }
  var R = Object.assign, h;
  function S(e) {
    if (h === void 0) try {
      throw Error();
    } catch (t) {
      var n = t.stack.trim().match(/\n( *(at )?)/);
      h = n && n[1] || "";
    }
    return `
` + h + e;
  }
  var Z = !1;
  function Y(e, n) {
    if (!e || Z) return "";
    Z = !0;
    var t = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      if (n) if (n = function() {
        throw Error();
      }, Object.defineProperty(n.prototype, "props", { set: function() {
        throw Error();
      } }), typeof Reflect == "object" && Reflect.construct) {
        try {
          Reflect.construct(n, []);
        } catch (g) {
          var r = g;
        }
        Reflect.construct(e, [], n);
      } else {
        try {
          n.call();
        } catch (g) {
          r = g;
        }
        e.call(n.prototype);
      }
      else {
        try {
          throw Error();
        } catch (g) {
          r = g;
        }
        e();
      }
    } catch (g) {
      if (g && r && typeof g.stack == "string") {
        for (var l = g.stack.split(`
`), i = r.stack.split(`
`), s = l.length - 1, d = i.length - 1; 1 <= s && 0 <= d && l[s] !== i[d]; ) d--;
        for (; 1 <= s && 0 <= d; s--, d--) if (l[s] !== i[d]) {
          if (s !== 1 || d !== 1)
            do
              if (s--, d--, 0 > d || l[s] !== i[d]) {
                var f = `
` + l[s].replace(" at new ", " at ");
                return e.displayName && f.includes("<anonymous>") && (f = f.replace("<anonymous>", e.displayName)), f;
              }
            while (1 <= s && 0 <= d);
          break;
        }
      }
    } finally {
      Z = !1, Error.prepareStackTrace = t;
    }
    return (e = e ? e.displayName || e.name : "") ? S(e) : "";
  }
  function $(e) {
    switch (e.tag) {
      case 5:
        return S(e.type);
      case 16:
        return S("Lazy");
      case 13:
        return S("Suspense");
      case 19:
        return S("SuspenseList");
      case 0:
      case 2:
      case 15:
        return e = Y(e.type, !1), e;
      case 11:
        return e = Y(e.type.render, !1), e;
      case 1:
        return e = Y(e.type, !0), e;
      default:
        return "";
    }
  }
  function ee(e) {
    if (e == null) return null;
    if (typeof e == "function") return e.displayName || e.name || null;
    if (typeof e == "string") return e;
    switch (e) {
      case G:
        return "Fragment";
      case we:
        return "Portal";
      case Xe:
        return "Profiler";
      case oe:
        return "StrictMode";
      case b:
        return "Suspense";
      case Ce:
        return "SuspenseList";
    }
    if (typeof e == "object") switch (e.$$typeof) {
      case Ve:
        return (e.displayName || "Context") + ".Consumer";
      case Fe:
        return (e._context.displayName || "Context") + ".Provider";
      case V:
        var n = e.render;
        return e = e.displayName, e || (e = n.displayName || n.name || "", e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef"), e;
      case Ue:
        return n = e.displayName || null, n !== null ? n : ee(e.type) || "Memo";
      case Me:
        n = e._payload, e = e._init;
        try {
          return ee(e(n));
        } catch {
        }
    }
    return null;
  }
  function se(e) {
    var n = e.type;
    switch (e.tag) {
      case 24:
        return "Cache";
      case 9:
        return (n.displayName || "Context") + ".Consumer";
      case 10:
        return (n._context.displayName || "Context") + ".Provider";
      case 18:
        return "DehydratedFragment";
      case 11:
        return e = n.render, e = e.displayName || e.name || "", n.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef");
      case 7:
        return "Fragment";
      case 5:
        return n;
      case 4:
        return "Portal";
      case 3:
        return "Root";
      case 6:
        return "Text";
      case 16:
        return ee(n);
      case 8:
        return n === oe ? "StrictMode" : "Mode";
      case 22:
        return "Offscreen";
      case 12:
        return "Profiler";
      case 21:
        return "Scope";
      case 13:
        return "Suspense";
      case 19:
        return "SuspenseList";
      case 25:
        return "TracingMarker";
      case 1:
      case 0:
      case 17:
      case 2:
      case 14:
      case 15:
        if (typeof n == "function") return n.displayName || n.name || null;
        if (typeof n == "string") return n;
    }
    return null;
  }
  function te(e) {
    switch (typeof e) {
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return e;
      case "object":
        return e;
      default:
        return "";
    }
  }
  function he(e) {
    var n = e.type;
    return (e = e.nodeName) && e.toLowerCase() === "input" && (n === "checkbox" || n === "radio");
  }
  function nn(e) {
    var n = he(e) ? "checked" : "value", t = Object.getOwnPropertyDescriptor(e.constructor.prototype, n), r = "" + e[n];
    if (!e.hasOwnProperty(n) && typeof t < "u" && typeof t.get == "function" && typeof t.set == "function") {
      var l = t.get, i = t.set;
      return Object.defineProperty(e, n, { configurable: !0, get: function() {
        return l.call(this);
      }, set: function(s) {
        r = "" + s, i.call(this, s);
      } }), Object.defineProperty(e, n, { enumerable: t.enumerable }), { getValue: function() {
        return r;
      }, setValue: function(s) {
        r = "" + s;
      }, stopTracking: function() {
        e._valueTracker = null, delete e[n];
      } };
    }
  }
  function Rr(e) {
    e._valueTracker || (e._valueTracker = nn(e));
  }
  function Ko(e) {
    if (!e) return !1;
    var n = e._valueTracker;
    if (!n) return !0;
    var t = n.getValue(), r = "";
    return e && (r = he(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== t ? (n.setValue(e), !0) : !1;
  }
  function Pr(e) {
    if (e = e || (typeof document < "u" ? document : void 0), typeof e > "u") return null;
    try {
      return e.activeElement || e.body;
    } catch {
      return e.body;
    }
  }
  function Xl(e, n) {
    var t = n.checked;
    return R({}, n, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: t ?? e._wrapperState.initialChecked });
  }
  function Qo(e, n) {
    var t = n.defaultValue == null ? "" : n.defaultValue, r = n.checked != null ? n.checked : n.defaultChecked;
    t = te(n.value != null ? n.value : t), e._wrapperState = { initialChecked: r, initialValue: t, controlled: n.type === "checkbox" || n.type === "radio" ? n.checked != null : n.value != null };
  }
  function Go(e, n) {
    n = n.checked, n != null && pe(e, "checked", n, !1);
  }
  function Zl(e, n) {
    Go(e, n);
    var t = te(n.value), r = n.type;
    if (t != null) r === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + t) : e.value !== "" + t && (e.value = "" + t);
    else if (r === "submit" || r === "reset") {
      e.removeAttribute("value");
      return;
    }
    n.hasOwnProperty("value") ? Jl(e, n.type, t) : n.hasOwnProperty("defaultValue") && Jl(e, n.type, te(n.defaultValue)), n.checked == null && n.defaultChecked != null && (e.defaultChecked = !!n.defaultChecked);
  }
  function Yo(e, n, t) {
    if (n.hasOwnProperty("value") || n.hasOwnProperty("defaultValue")) {
      var r = n.type;
      if (!(r !== "submit" && r !== "reset" || n.value !== void 0 && n.value !== null)) return;
      n = "" + e._wrapperState.initialValue, t || n === e.value || (e.value = n), e.defaultValue = n;
    }
    t = e.name, t !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, t !== "" && (e.name = t);
  }
  function Jl(e, n, t) {
    (n !== "number" || Pr(e.ownerDocument) !== e) && (t == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + t && (e.defaultValue = "" + t));
  }
  var Ut = Array.isArray;
  function ht(e, n, t, r) {
    if (e = e.options, n) {
      n = {};
      for (var l = 0; l < t.length; l++) n["$" + t[l]] = !0;
      for (t = 0; t < e.length; t++) l = n.hasOwnProperty("$" + e[t].value), e[t].selected !== l && (e[t].selected = l), l && r && (e[t].defaultSelected = !0);
    } else {
      for (t = "" + te(t), n = null, l = 0; l < e.length; l++) {
        if (e[l].value === t) {
          e[l].selected = !0, r && (e[l].defaultSelected = !0);
          return;
        }
        n !== null || e[l].disabled || (n = e[l]);
      }
      n !== null && (n.selected = !0);
    }
  }
  function Kl(e, n) {
    if (n.dangerouslySetInnerHTML != null) throw Error(c(91));
    return R({}, n, { value: void 0, defaultValue: void 0, children: "" + e._wrapperState.initialValue });
  }
  function bo(e, n) {
    var t = n.value;
    if (t == null) {
      if (t = n.children, n = n.defaultValue, t != null) {
        if (n != null) throw Error(c(92));
        if (Ut(t)) {
          if (1 < t.length) throw Error(c(93));
          t = t[0];
        }
        n = t;
      }
      n == null && (n = ""), t = n;
    }
    e._wrapperState = { initialValue: te(t) };
  }
  function _o(e, n) {
    var t = te(n.value), r = te(n.defaultValue);
    t != null && (t = "" + t, t !== e.value && (e.value = t), n.defaultValue == null && e.defaultValue !== t && (e.defaultValue = t)), r != null && (e.defaultValue = "" + r);
  }
  function $o(e) {
    var n = e.textContent;
    n === e._wrapperState.initialValue && n !== "" && n !== null && (e.value = n);
  }
  function es(e) {
    switch (e) {
      case "svg":
        return "http://www.w3.org/2000/svg";
      case "math":
        return "http://www.w3.org/1998/Math/MathML";
      default:
        return "http://www.w3.org/1999/xhtml";
    }
  }
  function Ql(e, n) {
    return e == null || e === "http://www.w3.org/1999/xhtml" ? es(n) : e === "http://www.w3.org/2000/svg" && n === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
  }
  var Tr, ns = (function(e) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(n, t, r, l) {
      MSApp.execUnsafeLocalFunction(function() {
        return e(n, t, r, l);
      });
    } : e;
  })(function(e, n) {
    if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = n;
    else {
      for (Tr = Tr || document.createElement("div"), Tr.innerHTML = "<svg>" + n.valueOf().toString() + "</svg>", n = Tr.firstChild; e.firstChild; ) e.removeChild(e.firstChild);
      for (; n.firstChild; ) e.appendChild(n.firstChild);
    }
  });
  function qt(e, n) {
    if (n) {
      var t = e.firstChild;
      if (t && t === e.lastChild && t.nodeType === 3) {
        t.nodeValue = n;
        return;
      }
    }
    e.textContent = n;
  }
  var Ht = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0
  }, pc = ["Webkit", "ms", "Moz", "O"];
  Object.keys(Ht).forEach(function(e) {
    pc.forEach(function(n) {
      n = n + e.charAt(0).toUpperCase() + e.substring(1), Ht[n] = Ht[e];
    });
  });
  function ts(e, n, t) {
    return n == null || typeof n == "boolean" || n === "" ? "" : t || typeof n != "number" || n === 0 || Ht.hasOwnProperty(e) && Ht[e] ? ("" + n).trim() : n + "px";
  }
  function rs(e, n) {
    e = e.style;
    for (var t in n) if (n.hasOwnProperty(t)) {
      var r = t.indexOf("--") === 0, l = ts(t, n[t], r);
      t === "float" && (t = "cssFloat"), r ? e.setProperty(t, l) : e[t] = l;
    }
  }
  var hc = R({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
  function Gl(e, n) {
    if (n) {
      if (hc[e] && (n.children != null || n.dangerouslySetInnerHTML != null)) throw Error(c(137, e));
      if (n.dangerouslySetInnerHTML != null) {
        if (n.children != null) throw Error(c(60));
        if (typeof n.dangerouslySetInnerHTML != "object" || !("__html" in n.dangerouslySetInnerHTML)) throw Error(c(61));
      }
      if (n.style != null && typeof n.style != "object") throw Error(c(62));
    }
  }
  function Yl(e, n) {
    if (e.indexOf("-") === -1) return typeof n.is == "string";
    switch (e) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var bl = null;
  function _l(e) {
    return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
  }
  var $l = null, mt = null, vt = null;
  function ls(e) {
    if (e = ar(e)) {
      if (typeof $l != "function") throw Error(c(280));
      var n = e.stateNode;
      n && (n = $r(n), $l(e.stateNode, e.type, n));
    }
  }
  function is(e) {
    mt ? vt ? vt.push(e) : vt = [e] : mt = e;
  }
  function os() {
    if (mt) {
      var e = mt, n = vt;
      if (vt = mt = null, ls(e), n) for (e = 0; e < n.length; e++) ls(n[e]);
    }
  }
  function ss(e, n) {
    return e(n);
  }
  function us() {
  }
  var ei = !1;
  function as(e, n, t) {
    if (ei) return e(n, t);
    ei = !0;
    try {
      return ss(e, n, t);
    } finally {
      ei = !1, (mt !== null || vt !== null) && (us(), os());
    }
  }
  function At(e, n) {
    var t = e.stateNode;
    if (t === null) return null;
    var r = $r(t);
    if (r === null) return null;
    t = r[n];
    e: switch (n) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (r = !r.disabled) || (e = e.type, r = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !r;
        break e;
      default:
        e = !1;
    }
    if (e) return null;
    if (t && typeof t != "function") throw Error(c(231, n, typeof t));
    return t;
  }
  var ni = !1;
  if (L) try {
    var Bt = {};
    Object.defineProperty(Bt, "passive", { get: function() {
      ni = !0;
    } }), window.addEventListener("test", Bt, Bt), window.removeEventListener("test", Bt, Bt);
  } catch {
    ni = !1;
  }
  function mc(e, n, t, r, l, i, s, d, f) {
    var g = Array.prototype.slice.call(arguments, 3);
    try {
      n.apply(t, g);
    } catch (N) {
      this.onError(N);
    }
  }
  var Xt = !1, Lr = null, Or = !1, ti = null, vc = { onError: function(e) {
    Xt = !0, Lr = e;
  } };
  function gc(e, n, t, r, l, i, s, d, f) {
    Xt = !1, Lr = null, mc.apply(vc, arguments);
  }
  function yc(e, n, t, r, l, i, s, d, f) {
    if (gc.apply(this, arguments), Xt) {
      if (Xt) {
        var g = Lr;
        Xt = !1, Lr = null;
      } else throw Error(c(198));
      Or || (Or = !0, ti = g);
    }
  }
  function nt(e) {
    var n = e, t = e;
    if (e.alternate) for (; n.return; ) n = n.return;
    else {
      e = n;
      do
        n = e, (n.flags & 4098) !== 0 && (t = n.return), e = n.return;
      while (e);
    }
    return n.tag === 3 ? t : null;
  }
  function cs(e) {
    if (e.tag === 13) {
      var n = e.memoizedState;
      if (n === null && (e = e.alternate, e !== null && (n = e.memoizedState)), n !== null) return n.dehydrated;
    }
    return null;
  }
  function ds(e) {
    if (nt(e) !== e) throw Error(c(188));
  }
  function xc(e) {
    var n = e.alternate;
    if (!n) {
      if (n = nt(e), n === null) throw Error(c(188));
      return n !== e ? null : e;
    }
    for (var t = e, r = n; ; ) {
      var l = t.return;
      if (l === null) break;
      var i = l.alternate;
      if (i === null) {
        if (r = l.return, r !== null) {
          t = r;
          continue;
        }
        break;
      }
      if (l.child === i.child) {
        for (i = l.child; i; ) {
          if (i === t) return ds(l), e;
          if (i === r) return ds(l), n;
          i = i.sibling;
        }
        throw Error(c(188));
      }
      if (t.return !== r.return) t = l, r = i;
      else {
        for (var s = !1, d = l.child; d; ) {
          if (d === t) {
            s = !0, t = l, r = i;
            break;
          }
          if (d === r) {
            s = !0, r = l, t = i;
            break;
          }
          d = d.sibling;
        }
        if (!s) {
          for (d = i.child; d; ) {
            if (d === t) {
              s = !0, t = i, r = l;
              break;
            }
            if (d === r) {
              s = !0, r = i, t = l;
              break;
            }
            d = d.sibling;
          }
          if (!s) throw Error(c(189));
        }
      }
      if (t.alternate !== r) throw Error(c(190));
    }
    if (t.tag !== 3) throw Error(c(188));
    return t.stateNode.current === t ? e : n;
  }
  function fs(e) {
    return e = xc(e), e !== null ? ps(e) : null;
  }
  function ps(e) {
    if (e.tag === 5 || e.tag === 6) return e;
    for (e = e.child; e !== null; ) {
      var n = ps(e);
      if (n !== null) return n;
      e = e.sibling;
    }
    return null;
  }
  var hs = a.unstable_scheduleCallback, ms = a.unstable_cancelCallback, wc = a.unstable_shouldYield, kc = a.unstable_requestPaint, Se = a.unstable_now, Sc = a.unstable_getCurrentPriorityLevel, ri = a.unstable_ImmediatePriority, vs = a.unstable_UserBlockingPriority, Fr = a.unstable_NormalPriority, jc = a.unstable_LowPriority, gs = a.unstable_IdlePriority, Mr = null, Sn = null;
  function Nc(e) {
    if (Sn && typeof Sn.onCommitFiberRoot == "function") try {
      Sn.onCommitFiberRoot(Mr, e, void 0, (e.current.flags & 128) === 128);
    } catch {
    }
  }
  var hn = Math.clz32 ? Math.clz32 : zc, Ec = Math.log, Cc = Math.LN2;
  function zc(e) {
    return e >>>= 0, e === 0 ? 32 : 31 - (Ec(e) / Cc | 0) | 0;
  }
  var Ir = 64, Wr = 4194304;
  function Zt(e) {
    switch (e & -e) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return e & 4194240;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return e & 130023424;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 1073741824;
      default:
        return e;
    }
  }
  function Dr(e, n) {
    var t = e.pendingLanes;
    if (t === 0) return 0;
    var r = 0, l = e.suspendedLanes, i = e.pingedLanes, s = t & 268435455;
    if (s !== 0) {
      var d = s & ~l;
      d !== 0 ? r = Zt(d) : (i &= s, i !== 0 && (r = Zt(i)));
    } else s = t & ~l, s !== 0 ? r = Zt(s) : i !== 0 && (r = Zt(i));
    if (r === 0) return 0;
    if (n !== 0 && n !== r && (n & l) === 0 && (l = r & -r, i = n & -n, l >= i || l === 16 && (i & 4194240) !== 0)) return n;
    if ((r & 4) !== 0 && (r |= t & 16), n = e.entangledLanes, n !== 0) for (e = e.entanglements, n &= r; 0 < n; ) t = 31 - hn(n), l = 1 << t, r |= e[t], n &= ~l;
    return r;
  }
  function Rc(e, n) {
    switch (e) {
      case 1:
      case 2:
      case 4:
        return n + 250;
      case 8:
      case 16:
      case 32:
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return n + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return -1;
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function Pc(e, n) {
    for (var t = e.suspendedLanes, r = e.pingedLanes, l = e.expirationTimes, i = e.pendingLanes; 0 < i; ) {
      var s = 31 - hn(i), d = 1 << s, f = l[s];
      f === -1 ? ((d & t) === 0 || (d & r) !== 0) && (l[s] = Rc(d, n)) : f <= n && (e.expiredLanes |= d), i &= ~d;
    }
  }
  function li(e) {
    return e = e.pendingLanes & -1073741825, e !== 0 ? e : e & 1073741824 ? 1073741824 : 0;
  }
  function ys() {
    var e = Ir;
    return Ir <<= 1, (Ir & 4194240) === 0 && (Ir = 64), e;
  }
  function ii(e) {
    for (var n = [], t = 0; 31 > t; t++) n.push(e);
    return n;
  }
  function Jt(e, n, t) {
    e.pendingLanes |= n, n !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, n = 31 - hn(n), e[n] = t;
  }
  function Tc(e, n) {
    var t = e.pendingLanes & ~n;
    e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= n, e.mutableReadLanes &= n, e.entangledLanes &= n, n = e.entanglements;
    var r = e.eventTimes;
    for (e = e.expirationTimes; 0 < t; ) {
      var l = 31 - hn(t), i = 1 << l;
      n[l] = 0, r[l] = -1, e[l] = -1, t &= ~i;
    }
  }
  function oi(e, n) {
    var t = e.entangledLanes |= n;
    for (e = e.entanglements; t; ) {
      var r = 31 - hn(t), l = 1 << r;
      l & n | e[r] & n && (e[r] |= n), t &= ~l;
    }
  }
  var re = 0;
  function xs(e) {
    return e &= -e, 1 < e ? 4 < e ? (e & 268435455) !== 0 ? 16 : 536870912 : 4 : 1;
  }
  var ws, si, ks, Ss, js, ui = !1, Vr = [], In = null, Wn = null, Dn = null, Kt = /* @__PURE__ */ new Map(), Qt = /* @__PURE__ */ new Map(), Vn = [], Lc = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
  function Ns(e, n) {
    switch (e) {
      case "focusin":
      case "focusout":
        In = null;
        break;
      case "dragenter":
      case "dragleave":
        Wn = null;
        break;
      case "mouseover":
      case "mouseout":
        Dn = null;
        break;
      case "pointerover":
      case "pointerout":
        Kt.delete(n.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        Qt.delete(n.pointerId);
    }
  }
  function Gt(e, n, t, r, l, i) {
    return e === null || e.nativeEvent !== i ? (e = { blockedOn: n, domEventName: t, eventSystemFlags: r, nativeEvent: i, targetContainers: [l] }, n !== null && (n = ar(n), n !== null && si(n)), e) : (e.eventSystemFlags |= r, n = e.targetContainers, l !== null && n.indexOf(l) === -1 && n.push(l), e);
  }
  function Oc(e, n, t, r, l) {
    switch (n) {
      case "focusin":
        return In = Gt(In, e, n, t, r, l), !0;
      case "dragenter":
        return Wn = Gt(Wn, e, n, t, r, l), !0;
      case "mouseover":
        return Dn = Gt(Dn, e, n, t, r, l), !0;
      case "pointerover":
        var i = l.pointerId;
        return Kt.set(i, Gt(Kt.get(i) || null, e, n, t, r, l)), !0;
      case "gotpointercapture":
        return i = l.pointerId, Qt.set(i, Gt(Qt.get(i) || null, e, n, t, r, l)), !0;
    }
    return !1;
  }
  function Es(e) {
    var n = tt(e.target);
    if (n !== null) {
      var t = nt(n);
      if (t !== null) {
        if (n = t.tag, n === 13) {
          if (n = cs(t), n !== null) {
            e.blockedOn = n, js(e.priority, function() {
              ks(t);
            });
            return;
          }
        } else if (n === 3 && t.stateNode.current.memoizedState.isDehydrated) {
          e.blockedOn = t.tag === 3 ? t.stateNode.containerInfo : null;
          return;
        }
      }
    }
    e.blockedOn = null;
  }
  function Ur(e) {
    if (e.blockedOn !== null) return !1;
    for (var n = e.targetContainers; 0 < n.length; ) {
      var t = ci(e.domEventName, e.eventSystemFlags, n[0], e.nativeEvent);
      if (t === null) {
        t = e.nativeEvent;
        var r = new t.constructor(t.type, t);
        bl = r, t.target.dispatchEvent(r), bl = null;
      } else return n = ar(t), n !== null && si(n), e.blockedOn = t, !1;
      n.shift();
    }
    return !0;
  }
  function Cs(e, n, t) {
    Ur(e) && t.delete(n);
  }
  function Fc() {
    ui = !1, In !== null && Ur(In) && (In = null), Wn !== null && Ur(Wn) && (Wn = null), Dn !== null && Ur(Dn) && (Dn = null), Kt.forEach(Cs), Qt.forEach(Cs);
  }
  function Yt(e, n) {
    e.blockedOn === n && (e.blockedOn = null, ui || (ui = !0, a.unstable_scheduleCallback(a.unstable_NormalPriority, Fc)));
  }
  function bt(e) {
    function n(l) {
      return Yt(l, e);
    }
    if (0 < Vr.length) {
      Yt(Vr[0], e);
      for (var t = 1; t < Vr.length; t++) {
        var r = Vr[t];
        r.blockedOn === e && (r.blockedOn = null);
      }
    }
    for (In !== null && Yt(In, e), Wn !== null && Yt(Wn, e), Dn !== null && Yt(Dn, e), Kt.forEach(n), Qt.forEach(n), t = 0; t < Vn.length; t++) r = Vn[t], r.blockedOn === e && (r.blockedOn = null);
    for (; 0 < Vn.length && (t = Vn[0], t.blockedOn === null); ) Es(t), t.blockedOn === null && Vn.shift();
  }
  var gt = ge.ReactCurrentBatchConfig, qr = !0;
  function Mc(e, n, t, r) {
    var l = re, i = gt.transition;
    gt.transition = null;
    try {
      re = 1, ai(e, n, t, r);
    } finally {
      re = l, gt.transition = i;
    }
  }
  function Ic(e, n, t, r) {
    var l = re, i = gt.transition;
    gt.transition = null;
    try {
      re = 4, ai(e, n, t, r);
    } finally {
      re = l, gt.transition = i;
    }
  }
  function ai(e, n, t, r) {
    if (qr) {
      var l = ci(e, n, t, r);
      if (l === null) zi(e, n, r, Hr, t), Ns(e, r);
      else if (Oc(l, e, n, t, r)) r.stopPropagation();
      else if (Ns(e, r), n & 4 && -1 < Lc.indexOf(e)) {
        for (; l !== null; ) {
          var i = ar(l);
          if (i !== null && ws(i), i = ci(e, n, t, r), i === null && zi(e, n, r, Hr, t), i === l) break;
          l = i;
        }
        l !== null && r.stopPropagation();
      } else zi(e, n, r, null, t);
    }
  }
  var Hr = null;
  function ci(e, n, t, r) {
    if (Hr = null, e = _l(r), e = tt(e), e !== null) if (n = nt(e), n === null) e = null;
    else if (t = n.tag, t === 13) {
      if (e = cs(n), e !== null) return e;
      e = null;
    } else if (t === 3) {
      if (n.stateNode.current.memoizedState.isDehydrated) return n.tag === 3 ? n.stateNode.containerInfo : null;
      e = null;
    } else n !== e && (e = null);
    return Hr = e, null;
  }
  function zs(e) {
    switch (e) {
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 1;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "toggle":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 4;
      case "message":
        switch (Sc()) {
          case ri:
            return 1;
          case vs:
            return 4;
          case Fr:
          case jc:
            return 16;
          case gs:
            return 536870912;
          default:
            return 16;
        }
      default:
        return 16;
    }
  }
  var Un = null, di = null, Ar = null;
  function Rs() {
    if (Ar) return Ar;
    var e, n = di, t = n.length, r, l = "value" in Un ? Un.value : Un.textContent, i = l.length;
    for (e = 0; e < t && n[e] === l[e]; e++) ;
    var s = t - e;
    for (r = 1; r <= s && n[t - r] === l[i - r]; r++) ;
    return Ar = l.slice(e, 1 < r ? 1 - r : void 0);
  }
  function Br(e) {
    var n = e.keyCode;
    return "charCode" in e ? (e = e.charCode, e === 0 && n === 13 && (e = 13)) : e = n, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
  }
  function Xr() {
    return !0;
  }
  function Ps() {
    return !1;
  }
  function tn(e) {
    function n(t, r, l, i, s) {
      this._reactName = t, this._targetInst = l, this.type = r, this.nativeEvent = i, this.target = s, this.currentTarget = null;
      for (var d in e) e.hasOwnProperty(d) && (t = e[d], this[d] = t ? t(i) : i[d]);
      return this.isDefaultPrevented = (i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1) ? Xr : Ps, this.isPropagationStopped = Ps, this;
    }
    return R(n.prototype, { preventDefault: function() {
      this.defaultPrevented = !0;
      var t = this.nativeEvent;
      t && (t.preventDefault ? t.preventDefault() : typeof t.returnValue != "unknown" && (t.returnValue = !1), this.isDefaultPrevented = Xr);
    }, stopPropagation: function() {
      var t = this.nativeEvent;
      t && (t.stopPropagation ? t.stopPropagation() : typeof t.cancelBubble != "unknown" && (t.cancelBubble = !0), this.isPropagationStopped = Xr);
    }, persist: function() {
    }, isPersistent: Xr }), n;
  }
  var yt = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(e) {
    return e.timeStamp || Date.now();
  }, defaultPrevented: 0, isTrusted: 0 }, fi = tn(yt), _t = R({}, yt, { view: 0, detail: 0 }), Wc = tn(_t), pi, hi, $t, Zr = R({}, _t, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: vi, button: 0, buttons: 0, relatedTarget: function(e) {
    return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
  }, movementX: function(e) {
    return "movementX" in e ? e.movementX : (e !== $t && ($t && e.type === "mousemove" ? (pi = e.screenX - $t.screenX, hi = e.screenY - $t.screenY) : hi = pi = 0, $t = e), pi);
  }, movementY: function(e) {
    return "movementY" in e ? e.movementY : hi;
  } }), Ts = tn(Zr), Dc = R({}, Zr, { dataTransfer: 0 }), Vc = tn(Dc), Uc = R({}, _t, { relatedTarget: 0 }), mi = tn(Uc), qc = R({}, yt, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), Hc = tn(qc), Ac = R({}, yt, { clipboardData: function(e) {
    return "clipboardData" in e ? e.clipboardData : window.clipboardData;
  } }), Bc = tn(Ac), Xc = R({}, yt, { data: 0 }), Ls = tn(Xc), Zc = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, Jc = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, Kc = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
  function Qc(e) {
    var n = this.nativeEvent;
    return n.getModifierState ? n.getModifierState(e) : (e = Kc[e]) ? !!n[e] : !1;
  }
  function vi() {
    return Qc;
  }
  var Gc = R({}, _t, { key: function(e) {
    if (e.key) {
      var n = Zc[e.key] || e.key;
      if (n !== "Unidentified") return n;
    }
    return e.type === "keypress" ? (e = Br(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Jc[e.keyCode] || "Unidentified" : "";
  }, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: vi, charCode: function(e) {
    return e.type === "keypress" ? Br(e) : 0;
  }, keyCode: function(e) {
    return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  }, which: function(e) {
    return e.type === "keypress" ? Br(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  } }), Yc = tn(Gc), bc = R({}, Zr, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Os = tn(bc), _c = R({}, _t, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: vi }), $c = tn(_c), ed = R({}, yt, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), nd = tn(ed), td = R({}, Zr, {
    deltaX: function(e) {
      return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
    },
    deltaY: function(e) {
      return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), rd = tn(td), ld = [9, 13, 27, 32], gi = L && "CompositionEvent" in window, er = null;
  L && "documentMode" in document && (er = document.documentMode);
  var id = L && "TextEvent" in window && !er, Fs = L && (!gi || er && 8 < er && 11 >= er), Ms = " ", Is = !1;
  function Ws(e, n) {
    switch (e) {
      case "keyup":
        return ld.indexOf(n.keyCode) !== -1;
      case "keydown":
        return n.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function Ds(e) {
    return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
  }
  var xt = !1;
  function od(e, n) {
    switch (e) {
      case "compositionend":
        return Ds(n);
      case "keypress":
        return n.which !== 32 ? null : (Is = !0, Ms);
      case "textInput":
        return e = n.data, e === Ms && Is ? null : e;
      default:
        return null;
    }
  }
  function sd(e, n) {
    if (xt) return e === "compositionend" || !gi && Ws(e, n) ? (e = Rs(), Ar = di = Un = null, xt = !1, e) : null;
    switch (e) {
      case "paste":
        return null;
      case "keypress":
        if (!(n.ctrlKey || n.altKey || n.metaKey) || n.ctrlKey && n.altKey) {
          if (n.char && 1 < n.char.length) return n.char;
          if (n.which) return String.fromCharCode(n.which);
        }
        return null;
      case "compositionend":
        return Fs && n.locale !== "ko" ? null : n.data;
      default:
        return null;
    }
  }
  var ud = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
  function Vs(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n === "input" ? !!ud[e.type] : n === "textarea";
  }
  function Us(e, n, t, r) {
    is(r), n = Yr(n, "onChange"), 0 < n.length && (t = new fi("onChange", "change", null, t, r), e.push({ event: t, listeners: n }));
  }
  var nr = null, tr = null;
  function ad(e) {
    ru(e, 0);
  }
  function Jr(e) {
    var n = Nt(e);
    if (Ko(n)) return e;
  }
  function cd(e, n) {
    if (e === "change") return n;
  }
  var qs = !1;
  if (L) {
    var yi;
    if (L) {
      var xi = "oninput" in document;
      if (!xi) {
        var Hs = document.createElement("div");
        Hs.setAttribute("oninput", "return;"), xi = typeof Hs.oninput == "function";
      }
      yi = xi;
    } else yi = !1;
    qs = yi && (!document.documentMode || 9 < document.documentMode);
  }
  function As() {
    nr && (nr.detachEvent("onpropertychange", Bs), tr = nr = null);
  }
  function Bs(e) {
    if (e.propertyName === "value" && Jr(tr)) {
      var n = [];
      Us(n, tr, e, _l(e)), as(ad, n);
    }
  }
  function dd(e, n, t) {
    e === "focusin" ? (As(), nr = n, tr = t, nr.attachEvent("onpropertychange", Bs)) : e === "focusout" && As();
  }
  function fd(e) {
    if (e === "selectionchange" || e === "keyup" || e === "keydown") return Jr(tr);
  }
  function pd(e, n) {
    if (e === "click") return Jr(n);
  }
  function hd(e, n) {
    if (e === "input" || e === "change") return Jr(n);
  }
  function md(e, n) {
    return e === n && (e !== 0 || 1 / e === 1 / n) || e !== e && n !== n;
  }
  var mn = typeof Object.is == "function" ? Object.is : md;
  function rr(e, n) {
    if (mn(e, n)) return !0;
    if (typeof e != "object" || e === null || typeof n != "object" || n === null) return !1;
    var t = Object.keys(e), r = Object.keys(n);
    if (t.length !== r.length) return !1;
    for (r = 0; r < t.length; r++) {
      var l = t[r];
      if (!z.call(n, l) || !mn(e[l], n[l])) return !1;
    }
    return !0;
  }
  function Xs(e) {
    for (; e && e.firstChild; ) e = e.firstChild;
    return e;
  }
  function Zs(e, n) {
    var t = Xs(e);
    e = 0;
    for (var r; t; ) {
      if (t.nodeType === 3) {
        if (r = e + t.textContent.length, e <= n && r >= n) return { node: t, offset: n - e };
        e = r;
      }
      e: {
        for (; t; ) {
          if (t.nextSibling) {
            t = t.nextSibling;
            break e;
          }
          t = t.parentNode;
        }
        t = void 0;
      }
      t = Xs(t);
    }
  }
  function Js(e, n) {
    return e && n ? e === n ? !0 : e && e.nodeType === 3 ? !1 : n && n.nodeType === 3 ? Js(e, n.parentNode) : "contains" in e ? e.contains(n) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(n) & 16) : !1 : !1;
  }
  function Ks() {
    for (var e = window, n = Pr(); n instanceof e.HTMLIFrameElement; ) {
      try {
        var t = typeof n.contentWindow.location.href == "string";
      } catch {
        t = !1;
      }
      if (t) e = n.contentWindow;
      else break;
      n = Pr(e.document);
    }
    return n;
  }
  function wi(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n && (n === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || n === "textarea" || e.contentEditable === "true");
  }
  function vd(e) {
    var n = Ks(), t = e.focusedElem, r = e.selectionRange;
    if (n !== t && t && t.ownerDocument && Js(t.ownerDocument.documentElement, t)) {
      if (r !== null && wi(t)) {
        if (n = r.start, e = r.end, e === void 0 && (e = n), "selectionStart" in t) t.selectionStart = n, t.selectionEnd = Math.min(e, t.value.length);
        else if (e = (n = t.ownerDocument || document) && n.defaultView || window, e.getSelection) {
          e = e.getSelection();
          var l = t.textContent.length, i = Math.min(r.start, l);
          r = r.end === void 0 ? i : Math.min(r.end, l), !e.extend && i > r && (l = r, r = i, i = l), l = Zs(t, i);
          var s = Zs(
            t,
            r
          );
          l && s && (e.rangeCount !== 1 || e.anchorNode !== l.node || e.anchorOffset !== l.offset || e.focusNode !== s.node || e.focusOffset !== s.offset) && (n = n.createRange(), n.setStart(l.node, l.offset), e.removeAllRanges(), i > r ? (e.addRange(n), e.extend(s.node, s.offset)) : (n.setEnd(s.node, s.offset), e.addRange(n)));
        }
      }
      for (n = [], e = t; e = e.parentNode; ) e.nodeType === 1 && n.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
      for (typeof t.focus == "function" && t.focus(), t = 0; t < n.length; t++) e = n[t], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
    }
  }
  var gd = L && "documentMode" in document && 11 >= document.documentMode, wt = null, ki = null, lr = null, Si = !1;
  function Qs(e, n, t) {
    var r = t.window === t ? t.document : t.nodeType === 9 ? t : t.ownerDocument;
    Si || wt == null || wt !== Pr(r) || (r = wt, "selectionStart" in r && wi(r) ? r = { start: r.selectionStart, end: r.selectionEnd } : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = { anchorNode: r.anchorNode, anchorOffset: r.anchorOffset, focusNode: r.focusNode, focusOffset: r.focusOffset }), lr && rr(lr, r) || (lr = r, r = Yr(ki, "onSelect"), 0 < r.length && (n = new fi("onSelect", "select", null, n, t), e.push({ event: n, listeners: r }), n.target = wt)));
  }
  function Kr(e, n) {
    var t = {};
    return t[e.toLowerCase()] = n.toLowerCase(), t["Webkit" + e] = "webkit" + n, t["Moz" + e] = "moz" + n, t;
  }
  var kt = { animationend: Kr("Animation", "AnimationEnd"), animationiteration: Kr("Animation", "AnimationIteration"), animationstart: Kr("Animation", "AnimationStart"), transitionend: Kr("Transition", "TransitionEnd") }, ji = {}, Gs = {};
  L && (Gs = document.createElement("div").style, "AnimationEvent" in window || (delete kt.animationend.animation, delete kt.animationiteration.animation, delete kt.animationstart.animation), "TransitionEvent" in window || delete kt.transitionend.transition);
  function Qr(e) {
    if (ji[e]) return ji[e];
    if (!kt[e]) return e;
    var n = kt[e], t;
    for (t in n) if (n.hasOwnProperty(t) && t in Gs) return ji[e] = n[t];
    return e;
  }
  var Ys = Qr("animationend"), bs = Qr("animationiteration"), _s = Qr("animationstart"), $s = Qr("transitionend"), eu = /* @__PURE__ */ new Map(), nu = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
  function qn(e, n) {
    eu.set(e, n), x(n, [e]);
  }
  for (var Ni = 0; Ni < nu.length; Ni++) {
    var Ei = nu[Ni], yd = Ei.toLowerCase(), xd = Ei[0].toUpperCase() + Ei.slice(1);
    qn(yd, "on" + xd);
  }
  qn(Ys, "onAnimationEnd"), qn(bs, "onAnimationIteration"), qn(_s, "onAnimationStart"), qn("dblclick", "onDoubleClick"), qn("focusin", "onFocus"), qn("focusout", "onBlur"), qn($s, "onTransitionEnd"), T("onMouseEnter", ["mouseout", "mouseover"]), T("onMouseLeave", ["mouseout", "mouseover"]), T("onPointerEnter", ["pointerout", "pointerover"]), T("onPointerLeave", ["pointerout", "pointerover"]), x("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), x("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), x("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]), x("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), x("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), x("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
  var ir = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), wd = new Set("cancel close invalid load scroll toggle".split(" ").concat(ir));
  function tu(e, n, t) {
    var r = e.type || "unknown-event";
    e.currentTarget = t, yc(r, n, void 0, e), e.currentTarget = null;
  }
  function ru(e, n) {
    n = (n & 4) !== 0;
    for (var t = 0; t < e.length; t++) {
      var r = e[t], l = r.event;
      r = r.listeners;
      e: {
        var i = void 0;
        if (n) for (var s = r.length - 1; 0 <= s; s--) {
          var d = r[s], f = d.instance, g = d.currentTarget;
          if (d = d.listener, f !== i && l.isPropagationStopped()) break e;
          tu(l, d, g), i = f;
        }
        else for (s = 0; s < r.length; s++) {
          if (d = r[s], f = d.instance, g = d.currentTarget, d = d.listener, f !== i && l.isPropagationStopped()) break e;
          tu(l, d, g), i = f;
        }
      }
    }
    if (Or) throw e = ti, Or = !1, ti = null, e;
  }
  function ce(e, n) {
    var t = n[Fi];
    t === void 0 && (t = n[Fi] = /* @__PURE__ */ new Set());
    var r = e + "__bubble";
    t.has(r) || (lu(n, e, 2, !1), t.add(r));
  }
  function Ci(e, n, t) {
    var r = 0;
    n && (r |= 4), lu(t, e, r, n);
  }
  var Gr = "_reactListening" + Math.random().toString(36).slice(2);
  function or(e) {
    if (!e[Gr]) {
      e[Gr] = !0, y.forEach(function(t) {
        t !== "selectionchange" && (wd.has(t) || Ci(t, !1, e), Ci(t, !0, e));
      });
      var n = e.nodeType === 9 ? e : e.ownerDocument;
      n === null || n[Gr] || (n[Gr] = !0, Ci("selectionchange", !1, n));
    }
  }
  function lu(e, n, t, r) {
    switch (zs(n)) {
      case 1:
        var l = Mc;
        break;
      case 4:
        l = Ic;
        break;
      default:
        l = ai;
    }
    t = l.bind(null, n, t, e), l = void 0, !ni || n !== "touchstart" && n !== "touchmove" && n !== "wheel" || (l = !0), r ? l !== void 0 ? e.addEventListener(n, t, { capture: !0, passive: l }) : e.addEventListener(n, t, !0) : l !== void 0 ? e.addEventListener(n, t, { passive: l }) : e.addEventListener(n, t, !1);
  }
  function zi(e, n, t, r, l) {
    var i = r;
    if ((n & 1) === 0 && (n & 2) === 0 && r !== null) e: for (; ; ) {
      if (r === null) return;
      var s = r.tag;
      if (s === 3 || s === 4) {
        var d = r.stateNode.containerInfo;
        if (d === l || d.nodeType === 8 && d.parentNode === l) break;
        if (s === 4) for (s = r.return; s !== null; ) {
          var f = s.tag;
          if ((f === 3 || f === 4) && (f = s.stateNode.containerInfo, f === l || f.nodeType === 8 && f.parentNode === l)) return;
          s = s.return;
        }
        for (; d !== null; ) {
          if (s = tt(d), s === null) return;
          if (f = s.tag, f === 5 || f === 6) {
            r = i = s;
            continue e;
          }
          d = d.parentNode;
        }
      }
      r = r.return;
    }
    as(function() {
      var g = i, N = _l(t), E = [];
      e: {
        var j = eu.get(e);
        if (j !== void 0) {
          var F = fi, I = e;
          switch (e) {
            case "keypress":
              if (Br(t) === 0) break e;
            case "keydown":
            case "keyup":
              F = Yc;
              break;
            case "focusin":
              I = "focus", F = mi;
              break;
            case "focusout":
              I = "blur", F = mi;
              break;
            case "beforeblur":
            case "afterblur":
              F = mi;
              break;
            case "click":
              if (t.button === 2) break e;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              F = Ts;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              F = Vc;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              F = $c;
              break;
            case Ys:
            case bs:
            case _s:
              F = Hc;
              break;
            case $s:
              F = nd;
              break;
            case "scroll":
              F = Wc;
              break;
            case "wheel":
              F = rd;
              break;
            case "copy":
            case "cut":
            case "paste":
              F = Bc;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              F = Os;
          }
          var W = (n & 4) !== 0, je = !W && e === "scroll", m = W ? j !== null ? j + "Capture" : null : j;
          W = [];
          for (var p = g, v; p !== null; ) {
            v = p;
            var C = v.stateNode;
            if (v.tag === 5 && C !== null && (v = C, m !== null && (C = At(p, m), C != null && W.push(sr(p, C, v)))), je) break;
            p = p.return;
          }
          0 < W.length && (j = new F(j, I, null, t, N), E.push({ event: j, listeners: W }));
        }
      }
      if ((n & 7) === 0) {
        e: {
          if (j = e === "mouseover" || e === "pointerover", F = e === "mouseout" || e === "pointerout", j && t !== bl && (I = t.relatedTarget || t.fromElement) && (tt(I) || I[zn])) break e;
          if ((F || j) && (j = N.window === N ? N : (j = N.ownerDocument) ? j.defaultView || j.parentWindow : window, F ? (I = t.relatedTarget || t.toElement, F = g, I = I ? tt(I) : null, I !== null && (je = nt(I), I !== je || I.tag !== 5 && I.tag !== 6) && (I = null)) : (F = null, I = g), F !== I)) {
            if (W = Ts, C = "onMouseLeave", m = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (W = Os, C = "onPointerLeave", m = "onPointerEnter", p = "pointer"), je = F == null ? j : Nt(F), v = I == null ? j : Nt(I), j = new W(C, p + "leave", F, t, N), j.target = je, j.relatedTarget = v, C = null, tt(N) === g && (W = new W(m, p + "enter", I, t, N), W.target = v, W.relatedTarget = je, C = W), je = C, F && I) n: {
              for (W = F, m = I, p = 0, v = W; v; v = St(v)) p++;
              for (v = 0, C = m; C; C = St(C)) v++;
              for (; 0 < p - v; ) W = St(W), p--;
              for (; 0 < v - p; ) m = St(m), v--;
              for (; p--; ) {
                if (W === m || m !== null && W === m.alternate) break n;
                W = St(W), m = St(m);
              }
              W = null;
            }
            else W = null;
            F !== null && iu(E, j, F, W, !1), I !== null && je !== null && iu(E, je, I, W, !0);
          }
        }
        e: {
          if (j = g ? Nt(g) : window, F = j.nodeName && j.nodeName.toLowerCase(), F === "select" || F === "input" && j.type === "file") var D = cd;
          else if (Vs(j)) if (qs) D = hd;
          else {
            D = fd;
            var U = dd;
          }
          else (F = j.nodeName) && F.toLowerCase() === "input" && (j.type === "checkbox" || j.type === "radio") && (D = pd);
          if (D && (D = D(e, g))) {
            Us(E, D, t, N);
            break e;
          }
          U && U(e, j, g), e === "focusout" && (U = j._wrapperState) && U.controlled && j.type === "number" && Jl(j, "number", j.value);
        }
        switch (U = g ? Nt(g) : window, e) {
          case "focusin":
            (Vs(U) || U.contentEditable === "true") && (wt = U, ki = g, lr = null);
            break;
          case "focusout":
            lr = ki = wt = null;
            break;
          case "mousedown":
            Si = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            Si = !1, Qs(E, t, N);
            break;
          case "selectionchange":
            if (gd) break;
          case "keydown":
          case "keyup":
            Qs(E, t, N);
        }
        var q;
        if (gi) e: {
          switch (e) {
            case "compositionstart":
              var A = "onCompositionStart";
              break e;
            case "compositionend":
              A = "onCompositionEnd";
              break e;
            case "compositionupdate":
              A = "onCompositionUpdate";
              break e;
          }
          A = void 0;
        }
        else xt ? Ws(e, t) && (A = "onCompositionEnd") : e === "keydown" && t.keyCode === 229 && (A = "onCompositionStart");
        A && (Fs && t.locale !== "ko" && (xt || A !== "onCompositionStart" ? A === "onCompositionEnd" && xt && (q = Rs()) : (Un = N, di = "value" in Un ? Un.value : Un.textContent, xt = !0)), U = Yr(g, A), 0 < U.length && (A = new Ls(A, e, null, t, N), E.push({ event: A, listeners: U }), q ? A.data = q : (q = Ds(t), q !== null && (A.data = q)))), (q = id ? od(e, t) : sd(e, t)) && (g = Yr(g, "onBeforeInput"), 0 < g.length && (N = new Ls("onBeforeInput", "beforeinput", null, t, N), E.push({ event: N, listeners: g }), N.data = q));
      }
      ru(E, n);
    });
  }
  function sr(e, n, t) {
    return { instance: e, listener: n, currentTarget: t };
  }
  function Yr(e, n) {
    for (var t = n + "Capture", r = []; e !== null; ) {
      var l = e, i = l.stateNode;
      l.tag === 5 && i !== null && (l = i, i = At(e, t), i != null && r.unshift(sr(e, i, l)), i = At(e, n), i != null && r.push(sr(e, i, l))), e = e.return;
    }
    return r;
  }
  function St(e) {
    if (e === null) return null;
    do
      e = e.return;
    while (e && e.tag !== 5);
    return e || null;
  }
  function iu(e, n, t, r, l) {
    for (var i = n._reactName, s = []; t !== null && t !== r; ) {
      var d = t, f = d.alternate, g = d.stateNode;
      if (f !== null && f === r) break;
      d.tag === 5 && g !== null && (d = g, l ? (f = At(t, i), f != null && s.unshift(sr(t, f, d))) : l || (f = At(t, i), f != null && s.push(sr(t, f, d)))), t = t.return;
    }
    s.length !== 0 && e.push({ event: n, listeners: s });
  }
  var kd = /\r\n?/g, Sd = /\u0000|\uFFFD/g;
  function ou(e) {
    return (typeof e == "string" ? e : "" + e).replace(kd, `
`).replace(Sd, "");
  }
  function br(e, n, t) {
    if (n = ou(n), ou(e) !== n && t) throw Error(c(425));
  }
  function _r() {
  }
  var Ri = null, Pi = null;
  function Ti(e, n) {
    return e === "textarea" || e === "noscript" || typeof n.children == "string" || typeof n.children == "number" || typeof n.dangerouslySetInnerHTML == "object" && n.dangerouslySetInnerHTML !== null && n.dangerouslySetInnerHTML.__html != null;
  }
  var Li = typeof setTimeout == "function" ? setTimeout : void 0, jd = typeof clearTimeout == "function" ? clearTimeout : void 0, su = typeof Promise == "function" ? Promise : void 0, Nd = typeof queueMicrotask == "function" ? queueMicrotask : typeof su < "u" ? function(e) {
    return su.resolve(null).then(e).catch(Ed);
  } : Li;
  function Ed(e) {
    setTimeout(function() {
      throw e;
    });
  }
  function Oi(e, n) {
    var t = n, r = 0;
    do {
      var l = t.nextSibling;
      if (e.removeChild(t), l && l.nodeType === 8) if (t = l.data, t === "/$") {
        if (r === 0) {
          e.removeChild(l), bt(n);
          return;
        }
        r--;
      } else t !== "$" && t !== "$?" && t !== "$!" || r++;
      t = l;
    } while (t);
    bt(n);
  }
  function Hn(e) {
    for (; e != null; e = e.nextSibling) {
      var n = e.nodeType;
      if (n === 1 || n === 3) break;
      if (n === 8) {
        if (n = e.data, n === "$" || n === "$!" || n === "$?") break;
        if (n === "/$") return null;
      }
    }
    return e;
  }
  function uu(e) {
    e = e.previousSibling;
    for (var n = 0; e; ) {
      if (e.nodeType === 8) {
        var t = e.data;
        if (t === "$" || t === "$!" || t === "$?") {
          if (n === 0) return e;
          n--;
        } else t === "/$" && n++;
      }
      e = e.previousSibling;
    }
    return null;
  }
  var jt = Math.random().toString(36).slice(2), jn = "__reactFiber$" + jt, ur = "__reactProps$" + jt, zn = "__reactContainer$" + jt, Fi = "__reactEvents$" + jt, Cd = "__reactListeners$" + jt, zd = "__reactHandles$" + jt;
  function tt(e) {
    var n = e[jn];
    if (n) return n;
    for (var t = e.parentNode; t; ) {
      if (n = t[zn] || t[jn]) {
        if (t = n.alternate, n.child !== null || t !== null && t.child !== null) for (e = uu(e); e !== null; ) {
          if (t = e[jn]) return t;
          e = uu(e);
        }
        return n;
      }
      e = t, t = e.parentNode;
    }
    return null;
  }
  function ar(e) {
    return e = e[jn] || e[zn], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
  }
  function Nt(e) {
    if (e.tag === 5 || e.tag === 6) return e.stateNode;
    throw Error(c(33));
  }
  function $r(e) {
    return e[ur] || null;
  }
  var Mi = [], Et = -1;
  function An(e) {
    return { current: e };
  }
  function de(e) {
    0 > Et || (e.current = Mi[Et], Mi[Et] = null, Et--);
  }
  function ue(e, n) {
    Et++, Mi[Et] = e.current, e.current = n;
  }
  var Bn = {}, qe = An(Bn), Qe = An(!1), rt = Bn;
  function Ct(e, n) {
    var t = e.type.contextTypes;
    if (!t) return Bn;
    var r = e.stateNode;
    if (r && r.__reactInternalMemoizedUnmaskedChildContext === n) return r.__reactInternalMemoizedMaskedChildContext;
    var l = {}, i;
    for (i in t) l[i] = n[i];
    return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = n, e.__reactInternalMemoizedMaskedChildContext = l), l;
  }
  function Ge(e) {
    return e = e.childContextTypes, e != null;
  }
  function el() {
    de(Qe), de(qe);
  }
  function au(e, n, t) {
    if (qe.current !== Bn) throw Error(c(168));
    ue(qe, n), ue(Qe, t);
  }
  function cu(e, n, t) {
    var r = e.stateNode;
    if (n = n.childContextTypes, typeof r.getChildContext != "function") return t;
    r = r.getChildContext();
    for (var l in r) if (!(l in n)) throw Error(c(108, se(e) || "Unknown", l));
    return R({}, t, r);
  }
  function nl(e) {
    return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Bn, rt = qe.current, ue(qe, e), ue(Qe, Qe.current), !0;
  }
  function du(e, n, t) {
    var r = e.stateNode;
    if (!r) throw Error(c(169));
    t ? (e = cu(e, n, rt), r.__reactInternalMemoizedMergedChildContext = e, de(Qe), de(qe), ue(qe, e)) : de(Qe), ue(Qe, t);
  }
  var Rn = null, tl = !1, Ii = !1;
  function fu(e) {
    Rn === null ? Rn = [e] : Rn.push(e);
  }
  function Rd(e) {
    tl = !0, fu(e);
  }
  function Xn() {
    if (!Ii && Rn !== null) {
      Ii = !0;
      var e = 0, n = re;
      try {
        var t = Rn;
        for (re = 1; e < t.length; e++) {
          var r = t[e];
          do
            r = r(!0);
          while (r !== null);
        }
        Rn = null, tl = !1;
      } catch (l) {
        throw Rn !== null && (Rn = Rn.slice(e + 1)), hs(ri, Xn), l;
      } finally {
        re = n, Ii = !1;
      }
    }
    return null;
  }
  var zt = [], Rt = 0, rl = null, ll = 0, un = [], an = 0, lt = null, Pn = 1, Tn = "";
  function it(e, n) {
    zt[Rt++] = ll, zt[Rt++] = rl, rl = e, ll = n;
  }
  function pu(e, n, t) {
    un[an++] = Pn, un[an++] = Tn, un[an++] = lt, lt = e;
    var r = Pn;
    e = Tn;
    var l = 32 - hn(r) - 1;
    r &= ~(1 << l), t += 1;
    var i = 32 - hn(n) + l;
    if (30 < i) {
      var s = l - l % 5;
      i = (r & (1 << s) - 1).toString(32), r >>= s, l -= s, Pn = 1 << 32 - hn(n) + l | t << l | r, Tn = i + e;
    } else Pn = 1 << i | t << l | r, Tn = e;
  }
  function Wi(e) {
    e.return !== null && (it(e, 1), pu(e, 1, 0));
  }
  function Di(e) {
    for (; e === rl; ) rl = zt[--Rt], zt[Rt] = null, ll = zt[--Rt], zt[Rt] = null;
    for (; e === lt; ) lt = un[--an], un[an] = null, Tn = un[--an], un[an] = null, Pn = un[--an], un[an] = null;
  }
  var rn = null, ln = null, me = !1, vn = null;
  function hu(e, n) {
    var t = pn(5, null, null, 0);
    t.elementType = "DELETED", t.stateNode = n, t.return = e, n = e.deletions, n === null ? (e.deletions = [t], e.flags |= 16) : n.push(t);
  }
  function mu(e, n) {
    switch (e.tag) {
      case 5:
        var t = e.type;
        return n = n.nodeType !== 1 || t.toLowerCase() !== n.nodeName.toLowerCase() ? null : n, n !== null ? (e.stateNode = n, rn = e, ln = Hn(n.firstChild), !0) : !1;
      case 6:
        return n = e.pendingProps === "" || n.nodeType !== 3 ? null : n, n !== null ? (e.stateNode = n, rn = e, ln = null, !0) : !1;
      case 13:
        return n = n.nodeType !== 8 ? null : n, n !== null ? (t = lt !== null ? { id: Pn, overflow: Tn } : null, e.memoizedState = { dehydrated: n, treeContext: t, retryLane: 1073741824 }, t = pn(18, null, null, 0), t.stateNode = n, t.return = e, e.child = t, rn = e, ln = null, !0) : !1;
      default:
        return !1;
    }
  }
  function Vi(e) {
    return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
  }
  function Ui(e) {
    if (me) {
      var n = ln;
      if (n) {
        var t = n;
        if (!mu(e, n)) {
          if (Vi(e)) throw Error(c(418));
          n = Hn(t.nextSibling);
          var r = rn;
          n && mu(e, n) ? hu(r, t) : (e.flags = e.flags & -4097 | 2, me = !1, rn = e);
        }
      } else {
        if (Vi(e)) throw Error(c(418));
        e.flags = e.flags & -4097 | 2, me = !1, rn = e;
      }
    }
  }
  function vu(e) {
    for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; ) e = e.return;
    rn = e;
  }
  function il(e) {
    if (e !== rn) return !1;
    if (!me) return vu(e), me = !0, !1;
    var n;
    if ((n = e.tag !== 3) && !(n = e.tag !== 5) && (n = e.type, n = n !== "head" && n !== "body" && !Ti(e.type, e.memoizedProps)), n && (n = ln)) {
      if (Vi(e)) throw gu(), Error(c(418));
      for (; n; ) hu(e, n), n = Hn(n.nextSibling);
    }
    if (vu(e), e.tag === 13) {
      if (e = e.memoizedState, e = e !== null ? e.dehydrated : null, !e) throw Error(c(317));
      e: {
        for (e = e.nextSibling, n = 0; e; ) {
          if (e.nodeType === 8) {
            var t = e.data;
            if (t === "/$") {
              if (n === 0) {
                ln = Hn(e.nextSibling);
                break e;
              }
              n--;
            } else t !== "$" && t !== "$!" && t !== "$?" || n++;
          }
          e = e.nextSibling;
        }
        ln = null;
      }
    } else ln = rn ? Hn(e.stateNode.nextSibling) : null;
    return !0;
  }
  function gu() {
    for (var e = ln; e; ) e = Hn(e.nextSibling);
  }
  function Pt() {
    ln = rn = null, me = !1;
  }
  function qi(e) {
    vn === null ? vn = [e] : vn.push(e);
  }
  var Pd = ge.ReactCurrentBatchConfig;
  function cr(e, n, t) {
    if (e = t.ref, e !== null && typeof e != "function" && typeof e != "object") {
      if (t._owner) {
        if (t = t._owner, t) {
          if (t.tag !== 1) throw Error(c(309));
          var r = t.stateNode;
        }
        if (!r) throw Error(c(147, e));
        var l = r, i = "" + e;
        return n !== null && n.ref !== null && typeof n.ref == "function" && n.ref._stringRef === i ? n.ref : (n = function(s) {
          var d = l.refs;
          s === null ? delete d[i] : d[i] = s;
        }, n._stringRef = i, n);
      }
      if (typeof e != "string") throw Error(c(284));
      if (!t._owner) throw Error(c(290, e));
    }
    return e;
  }
  function ol(e, n) {
    throw e = Object.prototype.toString.call(n), Error(c(31, e === "[object Object]" ? "object with keys {" + Object.keys(n).join(", ") + "}" : e));
  }
  function yu(e) {
    var n = e._init;
    return n(e._payload);
  }
  function xu(e) {
    function n(m, p) {
      if (e) {
        var v = m.deletions;
        v === null ? (m.deletions = [p], m.flags |= 16) : v.push(p);
      }
    }
    function t(m, p) {
      if (!e) return null;
      for (; p !== null; ) n(m, p), p = p.sibling;
      return null;
    }
    function r(m, p) {
      for (m = /* @__PURE__ */ new Map(); p !== null; ) p.key !== null ? m.set(p.key, p) : m.set(p.index, p), p = p.sibling;
      return m;
    }
    function l(m, p) {
      return m = _n(m, p), m.index = 0, m.sibling = null, m;
    }
    function i(m, p, v) {
      return m.index = v, e ? (v = m.alternate, v !== null ? (v = v.index, v < p ? (m.flags |= 2, p) : v) : (m.flags |= 2, p)) : (m.flags |= 1048576, p);
    }
    function s(m) {
      return e && m.alternate === null && (m.flags |= 2), m;
    }
    function d(m, p, v, C) {
      return p === null || p.tag !== 6 ? (p = Oo(v, m.mode, C), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function f(m, p, v, C) {
      var D = v.type;
      return D === G ? N(m, p, v.props.children, C, v.key) : p !== null && (p.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Me && yu(D) === p.type) ? (C = l(p, v.props), C.ref = cr(m, p, v), C.return = m, C) : (C = Tl(v.type, v.key, v.props, null, m.mode, C), C.ref = cr(m, p, v), C.return = m, C);
    }
    function g(m, p, v, C) {
      return p === null || p.tag !== 4 || p.stateNode.containerInfo !== v.containerInfo || p.stateNode.implementation !== v.implementation ? (p = Fo(v, m.mode, C), p.return = m, p) : (p = l(p, v.children || []), p.return = m, p);
    }
    function N(m, p, v, C, D) {
      return p === null || p.tag !== 7 ? (p = pt(v, m.mode, C, D), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function E(m, p, v) {
      if (typeof p == "string" && p !== "" || typeof p == "number") return p = Oo("" + p, m.mode, v), p.return = m, p;
      if (typeof p == "object" && p !== null) {
        switch (p.$$typeof) {
          case Pe:
            return v = Tl(p.type, p.key, p.props, null, m.mode, v), v.ref = cr(m, null, p), v.return = m, v;
          case we:
            return p = Fo(p, m.mode, v), p.return = m, p;
          case Me:
            var C = p._init;
            return E(m, C(p._payload), v);
        }
        if (Ut(p) || P(p)) return p = pt(p, m.mode, v, null), p.return = m, p;
        ol(m, p);
      }
      return null;
    }
    function j(m, p, v, C) {
      var D = p !== null ? p.key : null;
      if (typeof v == "string" && v !== "" || typeof v == "number") return D !== null ? null : d(m, p, "" + v, C);
      if (typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case Pe:
            return v.key === D ? f(m, p, v, C) : null;
          case we:
            return v.key === D ? g(m, p, v, C) : null;
          case Me:
            return D = v._init, j(
              m,
              p,
              D(v._payload),
              C
            );
        }
        if (Ut(v) || P(v)) return D !== null ? null : N(m, p, v, C, null);
        ol(m, v);
      }
      return null;
    }
    function F(m, p, v, C, D) {
      if (typeof C == "string" && C !== "" || typeof C == "number") return m = m.get(v) || null, d(p, m, "" + C, D);
      if (typeof C == "object" && C !== null) {
        switch (C.$$typeof) {
          case Pe:
            return m = m.get(C.key === null ? v : C.key) || null, f(p, m, C, D);
          case we:
            return m = m.get(C.key === null ? v : C.key) || null, g(p, m, C, D);
          case Me:
            var U = C._init;
            return F(m, p, v, U(C._payload), D);
        }
        if (Ut(C) || P(C)) return m = m.get(v) || null, N(p, m, C, D, null);
        ol(p, C);
      }
      return null;
    }
    function I(m, p, v, C) {
      for (var D = null, U = null, q = p, A = p = 0, Oe = null; q !== null && A < v.length; A++) {
        q.index > A ? (Oe = q, q = null) : Oe = q.sibling;
        var ne = j(m, q, v[A], C);
        if (ne === null) {
          q === null && (q = Oe);
          break;
        }
        e && q && ne.alternate === null && n(m, q), p = i(ne, p, A), U === null ? D = ne : U.sibling = ne, U = ne, q = Oe;
      }
      if (A === v.length) return t(m, q), me && it(m, A), D;
      if (q === null) {
        for (; A < v.length; A++) q = E(m, v[A], C), q !== null && (p = i(q, p, A), U === null ? D = q : U.sibling = q, U = q);
        return me && it(m, A), D;
      }
      for (q = r(m, q); A < v.length; A++) Oe = F(q, m, A, v[A], C), Oe !== null && (e && Oe.alternate !== null && q.delete(Oe.key === null ? A : Oe.key), p = i(Oe, p, A), U === null ? D = Oe : U.sibling = Oe, U = Oe);
      return e && q.forEach(function($n) {
        return n(m, $n);
      }), me && it(m, A), D;
    }
    function W(m, p, v, C) {
      var D = P(v);
      if (typeof D != "function") throw Error(c(150));
      if (v = D.call(v), v == null) throw Error(c(151));
      for (var U = D = null, q = p, A = p = 0, Oe = null, ne = v.next(); q !== null && !ne.done; A++, ne = v.next()) {
        q.index > A ? (Oe = q, q = null) : Oe = q.sibling;
        var $n = j(m, q, ne.value, C);
        if ($n === null) {
          q === null && (q = Oe);
          break;
        }
        e && q && $n.alternate === null && n(m, q), p = i($n, p, A), U === null ? D = $n : U.sibling = $n, U = $n, q = Oe;
      }
      if (ne.done) return t(
        m,
        q
      ), me && it(m, A), D;
      if (q === null) {
        for (; !ne.done; A++, ne = v.next()) ne = E(m, ne.value, C), ne !== null && (p = i(ne, p, A), U === null ? D = ne : U.sibling = ne, U = ne);
        return me && it(m, A), D;
      }
      for (q = r(m, q); !ne.done; A++, ne = v.next()) ne = F(q, m, A, ne.value, C), ne !== null && (e && ne.alternate !== null && q.delete(ne.key === null ? A : ne.key), p = i(ne, p, A), U === null ? D = ne : U.sibling = ne, U = ne);
      return e && q.forEach(function(af) {
        return n(m, af);
      }), me && it(m, A), D;
    }
    function je(m, p, v, C) {
      if (typeof v == "object" && v !== null && v.type === G && v.key === null && (v = v.props.children), typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case Pe:
            e: {
              for (var D = v.key, U = p; U !== null; ) {
                if (U.key === D) {
                  if (D = v.type, D === G) {
                    if (U.tag === 7) {
                      t(m, U.sibling), p = l(U, v.props.children), p.return = m, m = p;
                      break e;
                    }
                  } else if (U.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Me && yu(D) === U.type) {
                    t(m, U.sibling), p = l(U, v.props), p.ref = cr(m, U, v), p.return = m, m = p;
                    break e;
                  }
                  t(m, U);
                  break;
                } else n(m, U);
                U = U.sibling;
              }
              v.type === G ? (p = pt(v.props.children, m.mode, C, v.key), p.return = m, m = p) : (C = Tl(v.type, v.key, v.props, null, m.mode, C), C.ref = cr(m, p, v), C.return = m, m = C);
            }
            return s(m);
          case we:
            e: {
              for (U = v.key; p !== null; ) {
                if (p.key === U) if (p.tag === 4 && p.stateNode.containerInfo === v.containerInfo && p.stateNode.implementation === v.implementation) {
                  t(m, p.sibling), p = l(p, v.children || []), p.return = m, m = p;
                  break e;
                } else {
                  t(m, p);
                  break;
                }
                else n(m, p);
                p = p.sibling;
              }
              p = Fo(v, m.mode, C), p.return = m, m = p;
            }
            return s(m);
          case Me:
            return U = v._init, je(m, p, U(v._payload), C);
        }
        if (Ut(v)) return I(m, p, v, C);
        if (P(v)) return W(m, p, v, C);
        ol(m, v);
      }
      return typeof v == "string" && v !== "" || typeof v == "number" ? (v = "" + v, p !== null && p.tag === 6 ? (t(m, p.sibling), p = l(p, v), p.return = m, m = p) : (t(m, p), p = Oo(v, m.mode, C), p.return = m, m = p), s(m)) : t(m, p);
    }
    return je;
  }
  var Tt = xu(!0), wu = xu(!1), sl = An(null), ul = null, Lt = null, Hi = null;
  function Ai() {
    Hi = Lt = ul = null;
  }
  function Bi(e) {
    var n = sl.current;
    de(sl), e._currentValue = n;
  }
  function Xi(e, n, t) {
    for (; e !== null; ) {
      var r = e.alternate;
      if ((e.childLanes & n) !== n ? (e.childLanes |= n, r !== null && (r.childLanes |= n)) : r !== null && (r.childLanes & n) !== n && (r.childLanes |= n), e === t) break;
      e = e.return;
    }
  }
  function Ot(e, n) {
    ul = e, Hi = Lt = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & n) !== 0 && (Ye = !0), e.firstContext = null);
  }
  function cn(e) {
    var n = e._currentValue;
    if (Hi !== e) if (e = { context: e, memoizedValue: n, next: null }, Lt === null) {
      if (ul === null) throw Error(c(308));
      Lt = e, ul.dependencies = { lanes: 0, firstContext: e };
    } else Lt = Lt.next = e;
    return n;
  }
  var ot = null;
  function Zi(e) {
    ot === null ? ot = [e] : ot.push(e);
  }
  function ku(e, n, t, r) {
    var l = n.interleaved;
    return l === null ? (t.next = t, Zi(n)) : (t.next = l.next, l.next = t), n.interleaved = t, Ln(e, r);
  }
  function Ln(e, n) {
    e.lanes |= n;
    var t = e.alternate;
    for (t !== null && (t.lanes |= n), t = e, e = e.return; e !== null; ) e.childLanes |= n, t = e.alternate, t !== null && (t.childLanes |= n), t = e, e = e.return;
    return t.tag === 3 ? t.stateNode : null;
  }
  var Zn = !1;
  function Ji(e) {
    e.updateQueue = { baseState: e.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
  }
  function Su(e, n) {
    e = e.updateQueue, n.updateQueue === e && (n.updateQueue = { baseState: e.baseState, firstBaseUpdate: e.firstBaseUpdate, lastBaseUpdate: e.lastBaseUpdate, shared: e.shared, effects: e.effects });
  }
  function On(e, n) {
    return { eventTime: e, lane: n, tag: 0, payload: null, callback: null, next: null };
  }
  function Jn(e, n, t) {
    var r = e.updateQueue;
    if (r === null) return null;
    if (r = r.shared, (_ & 2) !== 0) {
      var l = r.pending;
      return l === null ? n.next = n : (n.next = l.next, l.next = n), r.pending = n, Ln(e, t);
    }
    return l = r.interleaved, l === null ? (n.next = n, Zi(r)) : (n.next = l.next, l.next = n), r.interleaved = n, Ln(e, t);
  }
  function al(e, n, t) {
    if (n = n.updateQueue, n !== null && (n = n.shared, (t & 4194240) !== 0)) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, oi(e, t);
    }
  }
  function ju(e, n) {
    var t = e.updateQueue, r = e.alternate;
    if (r !== null && (r = r.updateQueue, t === r)) {
      var l = null, i = null;
      if (t = t.firstBaseUpdate, t !== null) {
        do {
          var s = { eventTime: t.eventTime, lane: t.lane, tag: t.tag, payload: t.payload, callback: t.callback, next: null };
          i === null ? l = i = s : i = i.next = s, t = t.next;
        } while (t !== null);
        i === null ? l = i = n : i = i.next = n;
      } else l = i = n;
      t = { baseState: r.baseState, firstBaseUpdate: l, lastBaseUpdate: i, shared: r.shared, effects: r.effects }, e.updateQueue = t;
      return;
    }
    e = t.lastBaseUpdate, e === null ? t.firstBaseUpdate = n : e.next = n, t.lastBaseUpdate = n;
  }
  function cl(e, n, t, r) {
    var l = e.updateQueue;
    Zn = !1;
    var i = l.firstBaseUpdate, s = l.lastBaseUpdate, d = l.shared.pending;
    if (d !== null) {
      l.shared.pending = null;
      var f = d, g = f.next;
      f.next = null, s === null ? i = g : s.next = g, s = f;
      var N = e.alternate;
      N !== null && (N = N.updateQueue, d = N.lastBaseUpdate, d !== s && (d === null ? N.firstBaseUpdate = g : d.next = g, N.lastBaseUpdate = f));
    }
    if (i !== null) {
      var E = l.baseState;
      s = 0, N = g = f = null, d = i;
      do {
        var j = d.lane, F = d.eventTime;
        if ((r & j) === j) {
          N !== null && (N = N.next = {
            eventTime: F,
            lane: 0,
            tag: d.tag,
            payload: d.payload,
            callback: d.callback,
            next: null
          });
          e: {
            var I = e, W = d;
            switch (j = n, F = t, W.tag) {
              case 1:
                if (I = W.payload, typeof I == "function") {
                  E = I.call(F, E, j);
                  break e;
                }
                E = I;
                break e;
              case 3:
                I.flags = I.flags & -65537 | 128;
              case 0:
                if (I = W.payload, j = typeof I == "function" ? I.call(F, E, j) : I, j == null) break e;
                E = R({}, E, j);
                break e;
              case 2:
                Zn = !0;
            }
          }
          d.callback !== null && d.lane !== 0 && (e.flags |= 64, j = l.effects, j === null ? l.effects = [d] : j.push(d));
        } else F = { eventTime: F, lane: j, tag: d.tag, payload: d.payload, callback: d.callback, next: null }, N === null ? (g = N = F, f = E) : N = N.next = F, s |= j;
        if (d = d.next, d === null) {
          if (d = l.shared.pending, d === null) break;
          j = d, d = j.next, j.next = null, l.lastBaseUpdate = j, l.shared.pending = null;
        }
      } while (!0);
      if (N === null && (f = E), l.baseState = f, l.firstBaseUpdate = g, l.lastBaseUpdate = N, n = l.shared.interleaved, n !== null) {
        l = n;
        do
          s |= l.lane, l = l.next;
        while (l !== n);
      } else i === null && (l.shared.lanes = 0);
      at |= s, e.lanes = s, e.memoizedState = E;
    }
  }
  function Nu(e, n, t) {
    if (e = n.effects, n.effects = null, e !== null) for (n = 0; n < e.length; n++) {
      var r = e[n], l = r.callback;
      if (l !== null) {
        if (r.callback = null, r = t, typeof l != "function") throw Error(c(191, l));
        l.call(r);
      }
    }
  }
  var dr = {}, Nn = An(dr), fr = An(dr), pr = An(dr);
  function st(e) {
    if (e === dr) throw Error(c(174));
    return e;
  }
  function Ki(e, n) {
    switch (ue(pr, n), ue(fr, e), ue(Nn, dr), e = n.nodeType, e) {
      case 9:
      case 11:
        n = (n = n.documentElement) ? n.namespaceURI : Ql(null, "");
        break;
      default:
        e = e === 8 ? n.parentNode : n, n = e.namespaceURI || null, e = e.tagName, n = Ql(n, e);
    }
    de(Nn), ue(Nn, n);
  }
  function Ft() {
    de(Nn), de(fr), de(pr);
  }
  function Eu(e) {
    st(pr.current);
    var n = st(Nn.current), t = Ql(n, e.type);
    n !== t && (ue(fr, e), ue(Nn, t));
  }
  function Qi(e) {
    fr.current === e && (de(Nn), de(fr));
  }
  var ye = An(0);
  function dl(e) {
    for (var n = e; n !== null; ) {
      if (n.tag === 13) {
        var t = n.memoizedState;
        if (t !== null && (t = t.dehydrated, t === null || t.data === "$?" || t.data === "$!")) return n;
      } else if (n.tag === 19 && n.memoizedProps.revealOrder !== void 0) {
        if ((n.flags & 128) !== 0) return n;
      } else if (n.child !== null) {
        n.child.return = n, n = n.child;
        continue;
      }
      if (n === e) break;
      for (; n.sibling === null; ) {
        if (n.return === null || n.return === e) return null;
        n = n.return;
      }
      n.sibling.return = n.return, n = n.sibling;
    }
    return null;
  }
  var Gi = [];
  function Yi() {
    for (var e = 0; e < Gi.length; e++) Gi[e]._workInProgressVersionPrimary = null;
    Gi.length = 0;
  }
  var fl = ge.ReactCurrentDispatcher, bi = ge.ReactCurrentBatchConfig, ut = 0, xe = null, ze = null, Te = null, pl = !1, hr = !1, mr = 0, Td = 0;
  function He() {
    throw Error(c(321));
  }
  function _i(e, n) {
    if (n === null) return !1;
    for (var t = 0; t < n.length && t < e.length; t++) if (!mn(e[t], n[t])) return !1;
    return !0;
  }
  function $i(e, n, t, r, l, i) {
    if (ut = i, xe = n, n.memoizedState = null, n.updateQueue = null, n.lanes = 0, fl.current = e === null || e.memoizedState === null ? Md : Id, e = t(r, l), hr) {
      i = 0;
      do {
        if (hr = !1, mr = 0, 25 <= i) throw Error(c(301));
        i += 1, Te = ze = null, n.updateQueue = null, fl.current = Wd, e = t(r, l);
      } while (hr);
    }
    if (fl.current = vl, n = ze !== null && ze.next !== null, ut = 0, Te = ze = xe = null, pl = !1, n) throw Error(c(300));
    return e;
  }
  function eo() {
    var e = mr !== 0;
    return mr = 0, e;
  }
  function En() {
    var e = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
    return Te === null ? xe.memoizedState = Te = e : Te = Te.next = e, Te;
  }
  function dn() {
    if (ze === null) {
      var e = xe.alternate;
      e = e !== null ? e.memoizedState : null;
    } else e = ze.next;
    var n = Te === null ? xe.memoizedState : Te.next;
    if (n !== null) Te = n, ze = e;
    else {
      if (e === null) throw Error(c(310));
      ze = e, e = { memoizedState: ze.memoizedState, baseState: ze.baseState, baseQueue: ze.baseQueue, queue: ze.queue, next: null }, Te === null ? xe.memoizedState = Te = e : Te = Te.next = e;
    }
    return Te;
  }
  function vr(e, n) {
    return typeof n == "function" ? n(e) : n;
  }
  function no(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = ze, l = r.baseQueue, i = t.pending;
    if (i !== null) {
      if (l !== null) {
        var s = l.next;
        l.next = i.next, i.next = s;
      }
      r.baseQueue = l = i, t.pending = null;
    }
    if (l !== null) {
      i = l.next, r = r.baseState;
      var d = s = null, f = null, g = i;
      do {
        var N = g.lane;
        if ((ut & N) === N) f !== null && (f = f.next = { lane: 0, action: g.action, hasEagerState: g.hasEagerState, eagerState: g.eagerState, next: null }), r = g.hasEagerState ? g.eagerState : e(r, g.action);
        else {
          var E = {
            lane: N,
            action: g.action,
            hasEagerState: g.hasEagerState,
            eagerState: g.eagerState,
            next: null
          };
          f === null ? (d = f = E, s = r) : f = f.next = E, xe.lanes |= N, at |= N;
        }
        g = g.next;
      } while (g !== null && g !== i);
      f === null ? s = r : f.next = d, mn(r, n.memoizedState) || (Ye = !0), n.memoizedState = r, n.baseState = s, n.baseQueue = f, t.lastRenderedState = r;
    }
    if (e = t.interleaved, e !== null) {
      l = e;
      do
        i = l.lane, xe.lanes |= i, at |= i, l = l.next;
      while (l !== e);
    } else l === null && (t.lanes = 0);
    return [n.memoizedState, t.dispatch];
  }
  function to(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = t.dispatch, l = t.pending, i = n.memoizedState;
    if (l !== null) {
      t.pending = null;
      var s = l = l.next;
      do
        i = e(i, s.action), s = s.next;
      while (s !== l);
      mn(i, n.memoizedState) || (Ye = !0), n.memoizedState = i, n.baseQueue === null && (n.baseState = i), t.lastRenderedState = i;
    }
    return [i, r];
  }
  function Cu() {
  }
  function zu(e, n) {
    var t = xe, r = dn(), l = n(), i = !mn(r.memoizedState, l);
    if (i && (r.memoizedState = l, Ye = !0), r = r.queue, ro(Tu.bind(null, t, r, e), [e]), r.getSnapshot !== n || i || Te !== null && Te.memoizedState.tag & 1) {
      if (t.flags |= 2048, gr(9, Pu.bind(null, t, r, l, n), void 0, null), Le === null) throw Error(c(349));
      (ut & 30) !== 0 || Ru(t, n, l);
    }
    return l;
  }
  function Ru(e, n, t) {
    e.flags |= 16384, e = { getSnapshot: n, value: t }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.stores = [e]) : (t = n.stores, t === null ? n.stores = [e] : t.push(e));
  }
  function Pu(e, n, t, r) {
    n.value = t, n.getSnapshot = r, Lu(n) && Ou(e);
  }
  function Tu(e, n, t) {
    return t(function() {
      Lu(n) && Ou(e);
    });
  }
  function Lu(e) {
    var n = e.getSnapshot;
    e = e.value;
    try {
      var t = n();
      return !mn(e, t);
    } catch {
      return !0;
    }
  }
  function Ou(e) {
    var n = Ln(e, 1);
    n !== null && wn(n, e, 1, -1);
  }
  function Fu(e) {
    var n = En();
    return typeof e == "function" && (e = e()), n.memoizedState = n.baseState = e, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: vr, lastRenderedState: e }, n.queue = e, e = e.dispatch = Fd.bind(null, xe, e), [n.memoizedState, e];
  }
  function gr(e, n, t, r) {
    return e = { tag: e, create: n, destroy: t, deps: r, next: null }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.lastEffect = e.next = e) : (t = n.lastEffect, t === null ? n.lastEffect = e.next = e : (r = t.next, t.next = e, e.next = r, n.lastEffect = e)), e;
  }
  function Mu() {
    return dn().memoizedState;
  }
  function hl(e, n, t, r) {
    var l = En();
    xe.flags |= e, l.memoizedState = gr(1 | n, t, void 0, r === void 0 ? null : r);
  }
  function ml(e, n, t, r) {
    var l = dn();
    r = r === void 0 ? null : r;
    var i = void 0;
    if (ze !== null) {
      var s = ze.memoizedState;
      if (i = s.destroy, r !== null && _i(r, s.deps)) {
        l.memoizedState = gr(n, t, i, r);
        return;
      }
    }
    xe.flags |= e, l.memoizedState = gr(1 | n, t, i, r);
  }
  function Iu(e, n) {
    return hl(8390656, 8, e, n);
  }
  function ro(e, n) {
    return ml(2048, 8, e, n);
  }
  function Wu(e, n) {
    return ml(4, 2, e, n);
  }
  function Du(e, n) {
    return ml(4, 4, e, n);
  }
  function Vu(e, n) {
    if (typeof n == "function") return e = e(), n(e), function() {
      n(null);
    };
    if (n != null) return e = e(), n.current = e, function() {
      n.current = null;
    };
  }
  function Uu(e, n, t) {
    return t = t != null ? t.concat([e]) : null, ml(4, 4, Vu.bind(null, n, e), t);
  }
  function lo() {
  }
  function qu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && _i(n, r[1]) ? r[0] : (t.memoizedState = [e, n], e);
  }
  function Hu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && _i(n, r[1]) ? r[0] : (e = e(), t.memoizedState = [e, n], e);
  }
  function Au(e, n, t) {
    return (ut & 21) === 0 ? (e.baseState && (e.baseState = !1, Ye = !0), e.memoizedState = t) : (mn(t, n) || (t = ys(), xe.lanes |= t, at |= t, e.baseState = !0), n);
  }
  function Ld(e, n) {
    var t = re;
    re = t !== 0 && 4 > t ? t : 4, e(!0);
    var r = bi.transition;
    bi.transition = {};
    try {
      e(!1), n();
    } finally {
      re = t, bi.transition = r;
    }
  }
  function Bu() {
    return dn().memoizedState;
  }
  function Od(e, n, t) {
    var r = Yn(e);
    if (t = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null }, Xu(e)) Zu(n, t);
    else if (t = ku(e, n, t, r), t !== null) {
      var l = Je();
      wn(t, e, r, l), Ju(t, n, r);
    }
  }
  function Fd(e, n, t) {
    var r = Yn(e), l = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null };
    if (Xu(e)) Zu(n, l);
    else {
      var i = e.alternate;
      if (e.lanes === 0 && (i === null || i.lanes === 0) && (i = n.lastRenderedReducer, i !== null)) try {
        var s = n.lastRenderedState, d = i(s, t);
        if (l.hasEagerState = !0, l.eagerState = d, mn(d, s)) {
          var f = n.interleaved;
          f === null ? (l.next = l, Zi(n)) : (l.next = f.next, f.next = l), n.interleaved = l;
          return;
        }
      } catch {
      } finally {
      }
      t = ku(e, n, l, r), t !== null && (l = Je(), wn(t, e, r, l), Ju(t, n, r));
    }
  }
  function Xu(e) {
    var n = e.alternate;
    return e === xe || n !== null && n === xe;
  }
  function Zu(e, n) {
    hr = pl = !0;
    var t = e.pending;
    t === null ? n.next = n : (n.next = t.next, t.next = n), e.pending = n;
  }
  function Ju(e, n, t) {
    if ((t & 4194240) !== 0) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, oi(e, t);
    }
  }
  var vl = { readContext: cn, useCallback: He, useContext: He, useEffect: He, useImperativeHandle: He, useInsertionEffect: He, useLayoutEffect: He, useMemo: He, useReducer: He, useRef: He, useState: He, useDebugValue: He, useDeferredValue: He, useTransition: He, useMutableSource: He, useSyncExternalStore: He, useId: He, unstable_isNewReconciler: !1 }, Md = { readContext: cn, useCallback: function(e, n) {
    return En().memoizedState = [e, n === void 0 ? null : n], e;
  }, useContext: cn, useEffect: Iu, useImperativeHandle: function(e, n, t) {
    return t = t != null ? t.concat([e]) : null, hl(
      4194308,
      4,
      Vu.bind(null, n, e),
      t
    );
  }, useLayoutEffect: function(e, n) {
    return hl(4194308, 4, e, n);
  }, useInsertionEffect: function(e, n) {
    return hl(4, 2, e, n);
  }, useMemo: function(e, n) {
    var t = En();
    return n = n === void 0 ? null : n, e = e(), t.memoizedState = [e, n], e;
  }, useReducer: function(e, n, t) {
    var r = En();
    return n = t !== void 0 ? t(n) : n, r.memoizedState = r.baseState = n, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: e, lastRenderedState: n }, r.queue = e, e = e.dispatch = Od.bind(null, xe, e), [r.memoizedState, e];
  }, useRef: function(e) {
    var n = En();
    return e = { current: e }, n.memoizedState = e;
  }, useState: Fu, useDebugValue: lo, useDeferredValue: function(e) {
    return En().memoizedState = e;
  }, useTransition: function() {
    var e = Fu(!1), n = e[0];
    return e = Ld.bind(null, e[1]), En().memoizedState = e, [n, e];
  }, useMutableSource: function() {
  }, useSyncExternalStore: function(e, n, t) {
    var r = xe, l = En();
    if (me) {
      if (t === void 0) throw Error(c(407));
      t = t();
    } else {
      if (t = n(), Le === null) throw Error(c(349));
      (ut & 30) !== 0 || Ru(r, n, t);
    }
    l.memoizedState = t;
    var i = { value: t, getSnapshot: n };
    return l.queue = i, Iu(Tu.bind(
      null,
      r,
      i,
      e
    ), [e]), r.flags |= 2048, gr(9, Pu.bind(null, r, i, t, n), void 0, null), t;
  }, useId: function() {
    var e = En(), n = Le.identifierPrefix;
    if (me) {
      var t = Tn, r = Pn;
      t = (r & ~(1 << 32 - hn(r) - 1)).toString(32) + t, n = ":" + n + "R" + t, t = mr++, 0 < t && (n += "H" + t.toString(32)), n += ":";
    } else t = Td++, n = ":" + n + "r" + t.toString(32) + ":";
    return e.memoizedState = n;
  }, unstable_isNewReconciler: !1 }, Id = {
    readContext: cn,
    useCallback: qu,
    useContext: cn,
    useEffect: ro,
    useImperativeHandle: Uu,
    useInsertionEffect: Wu,
    useLayoutEffect: Du,
    useMemo: Hu,
    useReducer: no,
    useRef: Mu,
    useState: function() {
      return no(vr);
    },
    useDebugValue: lo,
    useDeferredValue: function(e) {
      var n = dn();
      return Au(n, ze.memoizedState, e);
    },
    useTransition: function() {
      var e = no(vr)[0], n = dn().memoizedState;
      return [e, n];
    },
    useMutableSource: Cu,
    useSyncExternalStore: zu,
    useId: Bu,
    unstable_isNewReconciler: !1
  }, Wd = { readContext: cn, useCallback: qu, useContext: cn, useEffect: ro, useImperativeHandle: Uu, useInsertionEffect: Wu, useLayoutEffect: Du, useMemo: Hu, useReducer: to, useRef: Mu, useState: function() {
    return to(vr);
  }, useDebugValue: lo, useDeferredValue: function(e) {
    var n = dn();
    return ze === null ? n.memoizedState = e : Au(n, ze.memoizedState, e);
  }, useTransition: function() {
    var e = to(vr)[0], n = dn().memoizedState;
    return [e, n];
  }, useMutableSource: Cu, useSyncExternalStore: zu, useId: Bu, unstable_isNewReconciler: !1 };
  function gn(e, n) {
    if (e && e.defaultProps) {
      n = R({}, n), e = e.defaultProps;
      for (var t in e) n[t] === void 0 && (n[t] = e[t]);
      return n;
    }
    return n;
  }
  function io(e, n, t, r) {
    n = e.memoizedState, t = t(r, n), t = t == null ? n : R({}, n, t), e.memoizedState = t, e.lanes === 0 && (e.updateQueue.baseState = t);
  }
  var gl = { isMounted: function(e) {
    return (e = e._reactInternals) ? nt(e) === e : !1;
  }, enqueueSetState: function(e, n, t) {
    e = e._reactInternals;
    var r = Je(), l = Yn(e), i = On(r, l);
    i.payload = n, t != null && (i.callback = t), n = Jn(e, i, l), n !== null && (wn(n, e, l, r), al(n, e, l));
  }, enqueueReplaceState: function(e, n, t) {
    e = e._reactInternals;
    var r = Je(), l = Yn(e), i = On(r, l);
    i.tag = 1, i.payload = n, t != null && (i.callback = t), n = Jn(e, i, l), n !== null && (wn(n, e, l, r), al(n, e, l));
  }, enqueueForceUpdate: function(e, n) {
    e = e._reactInternals;
    var t = Je(), r = Yn(e), l = On(t, r);
    l.tag = 2, n != null && (l.callback = n), n = Jn(e, l, r), n !== null && (wn(n, e, r, t), al(n, e, r));
  } };
  function Ku(e, n, t, r, l, i, s) {
    return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, i, s) : n.prototype && n.prototype.isPureReactComponent ? !rr(t, r) || !rr(l, i) : !0;
  }
  function Qu(e, n, t) {
    var r = !1, l = Bn, i = n.contextType;
    return typeof i == "object" && i !== null ? i = cn(i) : (l = Ge(n) ? rt : qe.current, r = n.contextTypes, i = (r = r != null) ? Ct(e, l) : Bn), n = new n(t, i), e.memoizedState = n.state !== null && n.state !== void 0 ? n.state : null, n.updater = gl, e.stateNode = n, n._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = l, e.__reactInternalMemoizedMaskedChildContext = i), n;
  }
  function Gu(e, n, t, r) {
    e = n.state, typeof n.componentWillReceiveProps == "function" && n.componentWillReceiveProps(t, r), typeof n.UNSAFE_componentWillReceiveProps == "function" && n.UNSAFE_componentWillReceiveProps(t, r), n.state !== e && gl.enqueueReplaceState(n, n.state, null);
  }
  function oo(e, n, t, r) {
    var l = e.stateNode;
    l.props = t, l.state = e.memoizedState, l.refs = {}, Ji(e);
    var i = n.contextType;
    typeof i == "object" && i !== null ? l.context = cn(i) : (i = Ge(n) ? rt : qe.current, l.context = Ct(e, i)), l.state = e.memoizedState, i = n.getDerivedStateFromProps, typeof i == "function" && (io(e, n, i, t), l.state = e.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof l.getSnapshotBeforeUpdate == "function" || typeof l.UNSAFE_componentWillMount != "function" && typeof l.componentWillMount != "function" || (n = l.state, typeof l.componentWillMount == "function" && l.componentWillMount(), typeof l.UNSAFE_componentWillMount == "function" && l.UNSAFE_componentWillMount(), n !== l.state && gl.enqueueReplaceState(l, l.state, null), cl(e, t, l, r), l.state = e.memoizedState), typeof l.componentDidMount == "function" && (e.flags |= 4194308);
  }
  function Mt(e, n) {
    try {
      var t = "", r = n;
      do
        t += $(r), r = r.return;
      while (r);
      var l = t;
    } catch (i) {
      l = `
Error generating stack: ` + i.message + `
` + i.stack;
    }
    return { value: e, source: n, stack: l, digest: null };
  }
  function so(e, n, t) {
    return { value: e, source: null, stack: t ?? null, digest: n ?? null };
  }
  function uo(e, n) {
    try {
      console.error(n.value);
    } catch (t) {
      setTimeout(function() {
        throw t;
      });
    }
  }
  var Dd = typeof WeakMap == "function" ? WeakMap : Map;
  function Yu(e, n, t) {
    t = On(-1, t), t.tag = 3, t.payload = { element: null };
    var r = n.value;
    return t.callback = function() {
      Nl || (Nl = !0, No = r), uo(e, n);
    }, t;
  }
  function bu(e, n, t) {
    t = On(-1, t), t.tag = 3;
    var r = e.type.getDerivedStateFromError;
    if (typeof r == "function") {
      var l = n.value;
      t.payload = function() {
        return r(l);
      }, t.callback = function() {
        uo(e, n);
      };
    }
    var i = e.stateNode;
    return i !== null && typeof i.componentDidCatch == "function" && (t.callback = function() {
      uo(e, n), typeof r != "function" && (Qn === null ? Qn = /* @__PURE__ */ new Set([this]) : Qn.add(this));
      var s = n.stack;
      this.componentDidCatch(n.value, { componentStack: s !== null ? s : "" });
    }), t;
  }
  function _u(e, n, t) {
    var r = e.pingCache;
    if (r === null) {
      r = e.pingCache = new Dd();
      var l = /* @__PURE__ */ new Set();
      r.set(n, l);
    } else l = r.get(n), l === void 0 && (l = /* @__PURE__ */ new Set(), r.set(n, l));
    l.has(t) || (l.add(t), e = bd.bind(null, e, n, t), n.then(e, e));
  }
  function $u(e) {
    do {
      var n;
      if ((n = e.tag === 13) && (n = e.memoizedState, n = n !== null ? n.dehydrated !== null : !0), n) return e;
      e = e.return;
    } while (e !== null);
    return null;
  }
  function ea(e, n, t, r, l) {
    return (e.mode & 1) === 0 ? (e === n ? e.flags |= 65536 : (e.flags |= 128, t.flags |= 131072, t.flags &= -52805, t.tag === 1 && (t.alternate === null ? t.tag = 17 : (n = On(-1, 1), n.tag = 2, Jn(t, n, 1))), t.lanes |= 1), e) : (e.flags |= 65536, e.lanes = l, e);
  }
  var Vd = ge.ReactCurrentOwner, Ye = !1;
  function Ze(e, n, t, r) {
    n.child = e === null ? wu(n, null, t, r) : Tt(n, e.child, t, r);
  }
  function na(e, n, t, r, l) {
    t = t.render;
    var i = n.ref;
    return Ot(n, l), r = $i(e, n, t, r, i, l), t = eo(), e !== null && !Ye ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (me && t && Wi(n), n.flags |= 1, Ze(e, n, r, l), n.child);
  }
  function ta(e, n, t, r, l) {
    if (e === null) {
      var i = t.type;
      return typeof i == "function" && !Lo(i) && i.defaultProps === void 0 && t.compare === null && t.defaultProps === void 0 ? (n.tag = 15, n.type = i, ra(e, n, i, r, l)) : (e = Tl(t.type, null, r, n, n.mode, l), e.ref = n.ref, e.return = n, n.child = e);
    }
    if (i = e.child, (e.lanes & l) === 0) {
      var s = i.memoizedProps;
      if (t = t.compare, t = t !== null ? t : rr, t(s, r) && e.ref === n.ref) return Fn(e, n, l);
    }
    return n.flags |= 1, e = _n(i, r), e.ref = n.ref, e.return = n, n.child = e;
  }
  function ra(e, n, t, r, l) {
    if (e !== null) {
      var i = e.memoizedProps;
      if (rr(i, r) && e.ref === n.ref) if (Ye = !1, n.pendingProps = r = i, (e.lanes & l) !== 0) (e.flags & 131072) !== 0 && (Ye = !0);
      else return n.lanes = e.lanes, Fn(e, n, l);
    }
    return ao(e, n, t, r, l);
  }
  function la(e, n, t) {
    var r = n.pendingProps, l = r.children, i = e !== null ? e.memoizedState : null;
    if (r.mode === "hidden") if ((n.mode & 1) === 0) n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, ue(Wt, on), on |= t;
    else {
      if ((t & 1073741824) === 0) return e = i !== null ? i.baseLanes | t : t, n.lanes = n.childLanes = 1073741824, n.memoizedState = { baseLanes: e, cachePool: null, transitions: null }, n.updateQueue = null, ue(Wt, on), on |= e, null;
      n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, r = i !== null ? i.baseLanes : t, ue(Wt, on), on |= r;
    }
    else i !== null ? (r = i.baseLanes | t, n.memoizedState = null) : r = t, ue(Wt, on), on |= r;
    return Ze(e, n, l, t), n.child;
  }
  function ia(e, n) {
    var t = n.ref;
    (e === null && t !== null || e !== null && e.ref !== t) && (n.flags |= 512, n.flags |= 2097152);
  }
  function ao(e, n, t, r, l) {
    var i = Ge(t) ? rt : qe.current;
    return i = Ct(n, i), Ot(n, l), t = $i(e, n, t, r, i, l), r = eo(), e !== null && !Ye ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (me && r && Wi(n), n.flags |= 1, Ze(e, n, t, l), n.child);
  }
  function oa(e, n, t, r, l) {
    if (Ge(t)) {
      var i = !0;
      nl(n);
    } else i = !1;
    if (Ot(n, l), n.stateNode === null) xl(e, n), Qu(n, t, r), oo(n, t, r, l), r = !0;
    else if (e === null) {
      var s = n.stateNode, d = n.memoizedProps;
      s.props = d;
      var f = s.context, g = t.contextType;
      typeof g == "object" && g !== null ? g = cn(g) : (g = Ge(t) ? rt : qe.current, g = Ct(n, g));
      var N = t.getDerivedStateFromProps, E = typeof N == "function" || typeof s.getSnapshotBeforeUpdate == "function";
      E || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== r || f !== g) && Gu(n, s, r, g), Zn = !1;
      var j = n.memoizedState;
      s.state = j, cl(n, r, s, l), f = n.memoizedState, d !== r || j !== f || Qe.current || Zn ? (typeof N == "function" && (io(n, t, N, r), f = n.memoizedState), (d = Zn || Ku(n, t, d, r, j, f, g)) ? (E || typeof s.UNSAFE_componentWillMount != "function" && typeof s.componentWillMount != "function" || (typeof s.componentWillMount == "function" && s.componentWillMount(), typeof s.UNSAFE_componentWillMount == "function" && s.UNSAFE_componentWillMount()), typeof s.componentDidMount == "function" && (n.flags |= 4194308)) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), n.memoizedProps = r, n.memoizedState = f), s.props = r, s.state = f, s.context = g, r = d) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), r = !1);
    } else {
      s = n.stateNode, Su(e, n), d = n.memoizedProps, g = n.type === n.elementType ? d : gn(n.type, d), s.props = g, E = n.pendingProps, j = s.context, f = t.contextType, typeof f == "object" && f !== null ? f = cn(f) : (f = Ge(t) ? rt : qe.current, f = Ct(n, f));
      var F = t.getDerivedStateFromProps;
      (N = typeof F == "function" || typeof s.getSnapshotBeforeUpdate == "function") || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== E || j !== f) && Gu(n, s, r, f), Zn = !1, j = n.memoizedState, s.state = j, cl(n, r, s, l);
      var I = n.memoizedState;
      d !== E || j !== I || Qe.current || Zn ? (typeof F == "function" && (io(n, t, F, r), I = n.memoizedState), (g = Zn || Ku(n, t, g, r, j, I, f) || !1) ? (N || typeof s.UNSAFE_componentWillUpdate != "function" && typeof s.componentWillUpdate != "function" || (typeof s.componentWillUpdate == "function" && s.componentWillUpdate(r, I, f), typeof s.UNSAFE_componentWillUpdate == "function" && s.UNSAFE_componentWillUpdate(r, I, f)), typeof s.componentDidUpdate == "function" && (n.flags |= 4), typeof s.getSnapshotBeforeUpdate == "function" && (n.flags |= 1024)) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), n.memoizedProps = r, n.memoizedState = I), s.props = r, s.state = I, s.context = f, r = g) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), r = !1);
    }
    return co(e, n, t, r, i, l);
  }
  function co(e, n, t, r, l, i) {
    ia(e, n);
    var s = (n.flags & 128) !== 0;
    if (!r && !s) return l && du(n, t, !1), Fn(e, n, i);
    r = n.stateNode, Vd.current = n;
    var d = s && typeof t.getDerivedStateFromError != "function" ? null : r.render();
    return n.flags |= 1, e !== null && s ? (n.child = Tt(n, e.child, null, i), n.child = Tt(n, null, d, i)) : Ze(e, n, d, i), n.memoizedState = r.state, l && du(n, t, !0), n.child;
  }
  function sa(e) {
    var n = e.stateNode;
    n.pendingContext ? au(e, n.pendingContext, n.pendingContext !== n.context) : n.context && au(e, n.context, !1), Ki(e, n.containerInfo);
  }
  function ua(e, n, t, r, l) {
    return Pt(), qi(l), n.flags |= 256, Ze(e, n, t, r), n.child;
  }
  var fo = { dehydrated: null, treeContext: null, retryLane: 0 };
  function po(e) {
    return { baseLanes: e, cachePool: null, transitions: null };
  }
  function aa(e, n, t) {
    var r = n.pendingProps, l = ye.current, i = !1, s = (n.flags & 128) !== 0, d;
    if ((d = s) || (d = e !== null && e.memoizedState === null ? !1 : (l & 2) !== 0), d ? (i = !0, n.flags &= -129) : (e === null || e.memoizedState !== null) && (l |= 1), ue(ye, l & 1), e === null)
      return Ui(n), e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? ((n.mode & 1) === 0 ? n.lanes = 1 : e.data === "$!" ? n.lanes = 8 : n.lanes = 1073741824, null) : (s = r.children, e = r.fallback, i ? (r = n.mode, i = n.child, s = { mode: "hidden", children: s }, (r & 1) === 0 && i !== null ? (i.childLanes = 0, i.pendingProps = s) : i = Ll(s, r, 0, null), e = pt(e, r, t, null), i.return = n, e.return = n, i.sibling = e, n.child = i, n.child.memoizedState = po(t), n.memoizedState = fo, e) : ho(n, s));
    if (l = e.memoizedState, l !== null && (d = l.dehydrated, d !== null)) return Ud(e, n, s, r, d, l, t);
    if (i) {
      i = r.fallback, s = n.mode, l = e.child, d = l.sibling;
      var f = { mode: "hidden", children: r.children };
      return (s & 1) === 0 && n.child !== l ? (r = n.child, r.childLanes = 0, r.pendingProps = f, n.deletions = null) : (r = _n(l, f), r.subtreeFlags = l.subtreeFlags & 14680064), d !== null ? i = _n(d, i) : (i = pt(i, s, t, null), i.flags |= 2), i.return = n, r.return = n, r.sibling = i, n.child = r, r = i, i = n.child, s = e.child.memoizedState, s = s === null ? po(t) : { baseLanes: s.baseLanes | t, cachePool: null, transitions: s.transitions }, i.memoizedState = s, i.childLanes = e.childLanes & ~t, n.memoizedState = fo, r;
    }
    return i = e.child, e = i.sibling, r = _n(i, { mode: "visible", children: r.children }), (n.mode & 1) === 0 && (r.lanes = t), r.return = n, r.sibling = null, e !== null && (t = n.deletions, t === null ? (n.deletions = [e], n.flags |= 16) : t.push(e)), n.child = r, n.memoizedState = null, r;
  }
  function ho(e, n) {
    return n = Ll({ mode: "visible", children: n }, e.mode, 0, null), n.return = e, e.child = n;
  }
  function yl(e, n, t, r) {
    return r !== null && qi(r), Tt(n, e.child, null, t), e = ho(n, n.pendingProps.children), e.flags |= 2, n.memoizedState = null, e;
  }
  function Ud(e, n, t, r, l, i, s) {
    if (t)
      return n.flags & 256 ? (n.flags &= -257, r = so(Error(c(422))), yl(e, n, s, r)) : n.memoizedState !== null ? (n.child = e.child, n.flags |= 128, null) : (i = r.fallback, l = n.mode, r = Ll({ mode: "visible", children: r.children }, l, 0, null), i = pt(i, l, s, null), i.flags |= 2, r.return = n, i.return = n, r.sibling = i, n.child = r, (n.mode & 1) !== 0 && Tt(n, e.child, null, s), n.child.memoizedState = po(s), n.memoizedState = fo, i);
    if ((n.mode & 1) === 0) return yl(e, n, s, null);
    if (l.data === "$!") {
      if (r = l.nextSibling && l.nextSibling.dataset, r) var d = r.dgst;
      return r = d, i = Error(c(419)), r = so(i, r, void 0), yl(e, n, s, r);
    }
    if (d = (s & e.childLanes) !== 0, Ye || d) {
      if (r = Le, r !== null) {
        switch (s & -s) {
          case 4:
            l = 2;
            break;
          case 16:
            l = 8;
            break;
          case 64:
          case 128:
          case 256:
          case 512:
          case 1024:
          case 2048:
          case 4096:
          case 8192:
          case 16384:
          case 32768:
          case 65536:
          case 131072:
          case 262144:
          case 524288:
          case 1048576:
          case 2097152:
          case 4194304:
          case 8388608:
          case 16777216:
          case 33554432:
          case 67108864:
            l = 32;
            break;
          case 536870912:
            l = 268435456;
            break;
          default:
            l = 0;
        }
        l = (l & (r.suspendedLanes | s)) !== 0 ? 0 : l, l !== 0 && l !== i.retryLane && (i.retryLane = l, Ln(e, l), wn(r, e, l, -1));
      }
      return To(), r = so(Error(c(421))), yl(e, n, s, r);
    }
    return l.data === "$?" ? (n.flags |= 128, n.child = e.child, n = _d.bind(null, e), l._reactRetry = n, null) : (e = i.treeContext, ln = Hn(l.nextSibling), rn = n, me = !0, vn = null, e !== null && (un[an++] = Pn, un[an++] = Tn, un[an++] = lt, Pn = e.id, Tn = e.overflow, lt = n), n = ho(n, r.children), n.flags |= 4096, n);
  }
  function ca(e, n, t) {
    e.lanes |= n;
    var r = e.alternate;
    r !== null && (r.lanes |= n), Xi(e.return, n, t);
  }
  function mo(e, n, t, r, l) {
    var i = e.memoizedState;
    i === null ? e.memoizedState = { isBackwards: n, rendering: null, renderingStartTime: 0, last: r, tail: t, tailMode: l } : (i.isBackwards = n, i.rendering = null, i.renderingStartTime = 0, i.last = r, i.tail = t, i.tailMode = l);
  }
  function da(e, n, t) {
    var r = n.pendingProps, l = r.revealOrder, i = r.tail;
    if (Ze(e, n, r.children, t), r = ye.current, (r & 2) !== 0) r = r & 1 | 2, n.flags |= 128;
    else {
      if (e !== null && (e.flags & 128) !== 0) e: for (e = n.child; e !== null; ) {
        if (e.tag === 13) e.memoizedState !== null && ca(e, t, n);
        else if (e.tag === 19) ca(e, t, n);
        else if (e.child !== null) {
          e.child.return = e, e = e.child;
          continue;
        }
        if (e === n) break e;
        for (; e.sibling === null; ) {
          if (e.return === null || e.return === n) break e;
          e = e.return;
        }
        e.sibling.return = e.return, e = e.sibling;
      }
      r &= 1;
    }
    if (ue(ye, r), (n.mode & 1) === 0) n.memoizedState = null;
    else switch (l) {
      case "forwards":
        for (t = n.child, l = null; t !== null; ) e = t.alternate, e !== null && dl(e) === null && (l = t), t = t.sibling;
        t = l, t === null ? (l = n.child, n.child = null) : (l = t.sibling, t.sibling = null), mo(n, !1, l, t, i);
        break;
      case "backwards":
        for (t = null, l = n.child, n.child = null; l !== null; ) {
          if (e = l.alternate, e !== null && dl(e) === null) {
            n.child = l;
            break;
          }
          e = l.sibling, l.sibling = t, t = l, l = e;
        }
        mo(n, !0, t, null, i);
        break;
      case "together":
        mo(n, !1, null, null, void 0);
        break;
      default:
        n.memoizedState = null;
    }
    return n.child;
  }
  function xl(e, n) {
    (n.mode & 1) === 0 && e !== null && (e.alternate = null, n.alternate = null, n.flags |= 2);
  }
  function Fn(e, n, t) {
    if (e !== null && (n.dependencies = e.dependencies), at |= n.lanes, (t & n.childLanes) === 0) return null;
    if (e !== null && n.child !== e.child) throw Error(c(153));
    if (n.child !== null) {
      for (e = n.child, t = _n(e, e.pendingProps), n.child = t, t.return = n; e.sibling !== null; ) e = e.sibling, t = t.sibling = _n(e, e.pendingProps), t.return = n;
      t.sibling = null;
    }
    return n.child;
  }
  function qd(e, n, t) {
    switch (n.tag) {
      case 3:
        sa(n), Pt();
        break;
      case 5:
        Eu(n);
        break;
      case 1:
        Ge(n.type) && nl(n);
        break;
      case 4:
        Ki(n, n.stateNode.containerInfo);
        break;
      case 10:
        var r = n.type._context, l = n.memoizedProps.value;
        ue(sl, r._currentValue), r._currentValue = l;
        break;
      case 13:
        if (r = n.memoizedState, r !== null)
          return r.dehydrated !== null ? (ue(ye, ye.current & 1), n.flags |= 128, null) : (t & n.child.childLanes) !== 0 ? aa(e, n, t) : (ue(ye, ye.current & 1), e = Fn(e, n, t), e !== null ? e.sibling : null);
        ue(ye, ye.current & 1);
        break;
      case 19:
        if (r = (t & n.childLanes) !== 0, (e.flags & 128) !== 0) {
          if (r) return da(e, n, t);
          n.flags |= 128;
        }
        if (l = n.memoizedState, l !== null && (l.rendering = null, l.tail = null, l.lastEffect = null), ue(ye, ye.current), r) break;
        return null;
      case 22:
      case 23:
        return n.lanes = 0, la(e, n, t);
    }
    return Fn(e, n, t);
  }
  var fa, vo, pa, ha;
  fa = function(e, n) {
    for (var t = n.child; t !== null; ) {
      if (t.tag === 5 || t.tag === 6) e.appendChild(t.stateNode);
      else if (t.tag !== 4 && t.child !== null) {
        t.child.return = t, t = t.child;
        continue;
      }
      if (t === n) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === n) return;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
  }, vo = function() {
  }, pa = function(e, n, t, r) {
    var l = e.memoizedProps;
    if (l !== r) {
      e = n.stateNode, st(Nn.current);
      var i = null;
      switch (t) {
        case "input":
          l = Xl(e, l), r = Xl(e, r), i = [];
          break;
        case "select":
          l = R({}, l, { value: void 0 }), r = R({}, r, { value: void 0 }), i = [];
          break;
        case "textarea":
          l = Kl(e, l), r = Kl(e, r), i = [];
          break;
        default:
          typeof l.onClick != "function" && typeof r.onClick == "function" && (e.onclick = _r);
      }
      Gl(t, r);
      var s;
      t = null;
      for (g in l) if (!r.hasOwnProperty(g) && l.hasOwnProperty(g) && l[g] != null) if (g === "style") {
        var d = l[g];
        for (s in d) d.hasOwnProperty(s) && (t || (t = {}), t[s] = "");
      } else g !== "dangerouslySetInnerHTML" && g !== "children" && g !== "suppressContentEditableWarning" && g !== "suppressHydrationWarning" && g !== "autoFocus" && (w.hasOwnProperty(g) ? i || (i = []) : (i = i || []).push(g, null));
      for (g in r) {
        var f = r[g];
        if (d = l != null ? l[g] : void 0, r.hasOwnProperty(g) && f !== d && (f != null || d != null)) if (g === "style") if (d) {
          for (s in d) !d.hasOwnProperty(s) || f && f.hasOwnProperty(s) || (t || (t = {}), t[s] = "");
          for (s in f) f.hasOwnProperty(s) && d[s] !== f[s] && (t || (t = {}), t[s] = f[s]);
        } else t || (i || (i = []), i.push(
          g,
          t
        )), t = f;
        else g === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, d = d ? d.__html : void 0, f != null && d !== f && (i = i || []).push(g, f)) : g === "children" ? typeof f != "string" && typeof f != "number" || (i = i || []).push(g, "" + f) : g !== "suppressContentEditableWarning" && g !== "suppressHydrationWarning" && (w.hasOwnProperty(g) ? (f != null && g === "onScroll" && ce("scroll", e), i || d === f || (i = [])) : (i = i || []).push(g, f));
      }
      t && (i = i || []).push("style", t);
      var g = i;
      (n.updateQueue = g) && (n.flags |= 4);
    }
  }, ha = function(e, n, t, r) {
    t !== r && (n.flags |= 4);
  };
  function yr(e, n) {
    if (!me) switch (e.tailMode) {
      case "hidden":
        n = e.tail;
        for (var t = null; n !== null; ) n.alternate !== null && (t = n), n = n.sibling;
        t === null ? e.tail = null : t.sibling = null;
        break;
      case "collapsed":
        t = e.tail;
        for (var r = null; t !== null; ) t.alternate !== null && (r = t), t = t.sibling;
        r === null ? n || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
    }
  }
  function Ae(e) {
    var n = e.alternate !== null && e.alternate.child === e.child, t = 0, r = 0;
    if (n) for (var l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags & 14680064, r |= l.flags & 14680064, l.return = e, l = l.sibling;
    else for (l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags, r |= l.flags, l.return = e, l = l.sibling;
    return e.subtreeFlags |= r, e.childLanes = t, n;
  }
  function Hd(e, n, t) {
    var r = n.pendingProps;
    switch (Di(n), n.tag) {
      case 2:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return Ae(n), null;
      case 1:
        return Ge(n.type) && el(), Ae(n), null;
      case 3:
        return r = n.stateNode, Ft(), de(Qe), de(qe), Yi(), r.pendingContext && (r.context = r.pendingContext, r.pendingContext = null), (e === null || e.child === null) && (il(n) ? n.flags |= 4 : e === null || e.memoizedState.isDehydrated && (n.flags & 256) === 0 || (n.flags |= 1024, vn !== null && (zo(vn), vn = null))), vo(e, n), Ae(n), null;
      case 5:
        Qi(n);
        var l = st(pr.current);
        if (t = n.type, e !== null && n.stateNode != null) pa(e, n, t, r, l), e.ref !== n.ref && (n.flags |= 512, n.flags |= 2097152);
        else {
          if (!r) {
            if (n.stateNode === null) throw Error(c(166));
            return Ae(n), null;
          }
          if (e = st(Nn.current), il(n)) {
            r = n.stateNode, t = n.type;
            var i = n.memoizedProps;
            switch (r[jn] = n, r[ur] = i, e = (n.mode & 1) !== 0, t) {
              case "dialog":
                ce("cancel", r), ce("close", r);
                break;
              case "iframe":
              case "object":
              case "embed":
                ce("load", r);
                break;
              case "video":
              case "audio":
                for (l = 0; l < ir.length; l++) ce(ir[l], r);
                break;
              case "source":
                ce("error", r);
                break;
              case "img":
              case "image":
              case "link":
                ce(
                  "error",
                  r
                ), ce("load", r);
                break;
              case "details":
                ce("toggle", r);
                break;
              case "input":
                Qo(r, i), ce("invalid", r);
                break;
              case "select":
                r._wrapperState = { wasMultiple: !!i.multiple }, ce("invalid", r);
                break;
              case "textarea":
                bo(r, i), ce("invalid", r);
            }
            Gl(t, i), l = null;
            for (var s in i) if (i.hasOwnProperty(s)) {
              var d = i[s];
              s === "children" ? typeof d == "string" ? r.textContent !== d && (i.suppressHydrationWarning !== !0 && br(r.textContent, d, e), l = ["children", d]) : typeof d == "number" && r.textContent !== "" + d && (i.suppressHydrationWarning !== !0 && br(
                r.textContent,
                d,
                e
              ), l = ["children", "" + d]) : w.hasOwnProperty(s) && d != null && s === "onScroll" && ce("scroll", r);
            }
            switch (t) {
              case "input":
                Rr(r), Yo(r, i, !0);
                break;
              case "textarea":
                Rr(r), $o(r);
                break;
              case "select":
              case "option":
                break;
              default:
                typeof i.onClick == "function" && (r.onclick = _r);
            }
            r = l, n.updateQueue = r, r !== null && (n.flags |= 4);
          } else {
            s = l.nodeType === 9 ? l : l.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = es(t)), e === "http://www.w3.org/1999/xhtml" ? t === "script" ? (e = s.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof r.is == "string" ? e = s.createElement(t, { is: r.is }) : (e = s.createElement(t), t === "select" && (s = e, r.multiple ? s.multiple = !0 : r.size && (s.size = r.size))) : e = s.createElementNS(e, t), e[jn] = n, e[ur] = r, fa(e, n, !1, !1), n.stateNode = e;
            e: {
              switch (s = Yl(t, r), t) {
                case "dialog":
                  ce("cancel", e), ce("close", e), l = r;
                  break;
                case "iframe":
                case "object":
                case "embed":
                  ce("load", e), l = r;
                  break;
                case "video":
                case "audio":
                  for (l = 0; l < ir.length; l++) ce(ir[l], e);
                  l = r;
                  break;
                case "source":
                  ce("error", e), l = r;
                  break;
                case "img":
                case "image":
                case "link":
                  ce(
                    "error",
                    e
                  ), ce("load", e), l = r;
                  break;
                case "details":
                  ce("toggle", e), l = r;
                  break;
                case "input":
                  Qo(e, r), l = Xl(e, r), ce("invalid", e);
                  break;
                case "option":
                  l = r;
                  break;
                case "select":
                  e._wrapperState = { wasMultiple: !!r.multiple }, l = R({}, r, { value: void 0 }), ce("invalid", e);
                  break;
                case "textarea":
                  bo(e, r), l = Kl(e, r), ce("invalid", e);
                  break;
                default:
                  l = r;
              }
              Gl(t, l), d = l;
              for (i in d) if (d.hasOwnProperty(i)) {
                var f = d[i];
                i === "style" ? rs(e, f) : i === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, f != null && ns(e, f)) : i === "children" ? typeof f == "string" ? (t !== "textarea" || f !== "") && qt(e, f) : typeof f == "number" && qt(e, "" + f) : i !== "suppressContentEditableWarning" && i !== "suppressHydrationWarning" && i !== "autoFocus" && (w.hasOwnProperty(i) ? f != null && i === "onScroll" && ce("scroll", e) : f != null && pe(e, i, f, s));
              }
              switch (t) {
                case "input":
                  Rr(e), Yo(e, r, !1);
                  break;
                case "textarea":
                  Rr(e), $o(e);
                  break;
                case "option":
                  r.value != null && e.setAttribute("value", "" + te(r.value));
                  break;
                case "select":
                  e.multiple = !!r.multiple, i = r.value, i != null ? ht(e, !!r.multiple, i, !1) : r.defaultValue != null && ht(
                    e,
                    !!r.multiple,
                    r.defaultValue,
                    !0
                  );
                  break;
                default:
                  typeof l.onClick == "function" && (e.onclick = _r);
              }
              switch (t) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  r = !!r.autoFocus;
                  break e;
                case "img":
                  r = !0;
                  break e;
                default:
                  r = !1;
              }
            }
            r && (n.flags |= 4);
          }
          n.ref !== null && (n.flags |= 512, n.flags |= 2097152);
        }
        return Ae(n), null;
      case 6:
        if (e && n.stateNode != null) ha(e, n, e.memoizedProps, r);
        else {
          if (typeof r != "string" && n.stateNode === null) throw Error(c(166));
          if (t = st(pr.current), st(Nn.current), il(n)) {
            if (r = n.stateNode, t = n.memoizedProps, r[jn] = n, (i = r.nodeValue !== t) && (e = rn, e !== null)) switch (e.tag) {
              case 3:
                br(r.nodeValue, t, (e.mode & 1) !== 0);
                break;
              case 5:
                e.memoizedProps.suppressHydrationWarning !== !0 && br(r.nodeValue, t, (e.mode & 1) !== 0);
            }
            i && (n.flags |= 4);
          } else r = (t.nodeType === 9 ? t : t.ownerDocument).createTextNode(r), r[jn] = n, n.stateNode = r;
        }
        return Ae(n), null;
      case 13:
        if (de(ye), r = n.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
          if (me && ln !== null && (n.mode & 1) !== 0 && (n.flags & 128) === 0) gu(), Pt(), n.flags |= 98560, i = !1;
          else if (i = il(n), r !== null && r.dehydrated !== null) {
            if (e === null) {
              if (!i) throw Error(c(318));
              if (i = n.memoizedState, i = i !== null ? i.dehydrated : null, !i) throw Error(c(317));
              i[jn] = n;
            } else Pt(), (n.flags & 128) === 0 && (n.memoizedState = null), n.flags |= 4;
            Ae(n), i = !1;
          } else vn !== null && (zo(vn), vn = null), i = !0;
          if (!i) return n.flags & 65536 ? n : null;
        }
        return (n.flags & 128) !== 0 ? (n.lanes = t, n) : (r = r !== null, r !== (e !== null && e.memoizedState !== null) && r && (n.child.flags |= 8192, (n.mode & 1) !== 0 && (e === null || (ye.current & 1) !== 0 ? Re === 0 && (Re = 3) : To())), n.updateQueue !== null && (n.flags |= 4), Ae(n), null);
      case 4:
        return Ft(), vo(e, n), e === null && or(n.stateNode.containerInfo), Ae(n), null;
      case 10:
        return Bi(n.type._context), Ae(n), null;
      case 17:
        return Ge(n.type) && el(), Ae(n), null;
      case 19:
        if (de(ye), i = n.memoizedState, i === null) return Ae(n), null;
        if (r = (n.flags & 128) !== 0, s = i.rendering, s === null) if (r) yr(i, !1);
        else {
          if (Re !== 0 || e !== null && (e.flags & 128) !== 0) for (e = n.child; e !== null; ) {
            if (s = dl(e), s !== null) {
              for (n.flags |= 128, yr(i, !1), r = s.updateQueue, r !== null && (n.updateQueue = r, n.flags |= 4), n.subtreeFlags = 0, r = t, t = n.child; t !== null; ) i = t, e = r, i.flags &= 14680066, s = i.alternate, s === null ? (i.childLanes = 0, i.lanes = e, i.child = null, i.subtreeFlags = 0, i.memoizedProps = null, i.memoizedState = null, i.updateQueue = null, i.dependencies = null, i.stateNode = null) : (i.childLanes = s.childLanes, i.lanes = s.lanes, i.child = s.child, i.subtreeFlags = 0, i.deletions = null, i.memoizedProps = s.memoizedProps, i.memoizedState = s.memoizedState, i.updateQueue = s.updateQueue, i.type = s.type, e = s.dependencies, i.dependencies = e === null ? null : { lanes: e.lanes, firstContext: e.firstContext }), t = t.sibling;
              return ue(ye, ye.current & 1 | 2), n.child;
            }
            e = e.sibling;
          }
          i.tail !== null && Se() > Dt && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
        }
        else {
          if (!r) if (e = dl(s), e !== null) {
            if (n.flags |= 128, r = !0, t = e.updateQueue, t !== null && (n.updateQueue = t, n.flags |= 4), yr(i, !0), i.tail === null && i.tailMode === "hidden" && !s.alternate && !me) return Ae(n), null;
          } else 2 * Se() - i.renderingStartTime > Dt && t !== 1073741824 && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
          i.isBackwards ? (s.sibling = n.child, n.child = s) : (t = i.last, t !== null ? t.sibling = s : n.child = s, i.last = s);
        }
        return i.tail !== null ? (n = i.tail, i.rendering = n, i.tail = n.sibling, i.renderingStartTime = Se(), n.sibling = null, t = ye.current, ue(ye, r ? t & 1 | 2 : t & 1), n) : (Ae(n), null);
      case 22:
      case 23:
        return Po(), r = n.memoizedState !== null, e !== null && e.memoizedState !== null !== r && (n.flags |= 8192), r && (n.mode & 1) !== 0 ? (on & 1073741824) !== 0 && (Ae(n), n.subtreeFlags & 6 && (n.flags |= 8192)) : Ae(n), null;
      case 24:
        return null;
      case 25:
        return null;
    }
    throw Error(c(156, n.tag));
  }
  function Ad(e, n) {
    switch (Di(n), n.tag) {
      case 1:
        return Ge(n.type) && el(), e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 3:
        return Ft(), de(Qe), de(qe), Yi(), e = n.flags, (e & 65536) !== 0 && (e & 128) === 0 ? (n.flags = e & -65537 | 128, n) : null;
      case 5:
        return Qi(n), null;
      case 13:
        if (de(ye), e = n.memoizedState, e !== null && e.dehydrated !== null) {
          if (n.alternate === null) throw Error(c(340));
          Pt();
        }
        return e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 19:
        return de(ye), null;
      case 4:
        return Ft(), null;
      case 10:
        return Bi(n.type._context), null;
      case 22:
      case 23:
        return Po(), null;
      case 24:
        return null;
      default:
        return null;
    }
  }
  var wl = !1, Be = !1, Bd = typeof WeakSet == "function" ? WeakSet : Set, M = null;
  function It(e, n) {
    var t = e.ref;
    if (t !== null) if (typeof t == "function") try {
      t(null);
    } catch (r) {
      ke(e, n, r);
    }
    else t.current = null;
  }
  function go(e, n, t) {
    try {
      t();
    } catch (r) {
      ke(e, n, r);
    }
  }
  var ma = !1;
  function Xd(e, n) {
    if (Ri = qr, e = Ks(), wi(e)) {
      if ("selectionStart" in e) var t = { start: e.selectionStart, end: e.selectionEnd };
      else e: {
        t = (t = e.ownerDocument) && t.defaultView || window;
        var r = t.getSelection && t.getSelection();
        if (r && r.rangeCount !== 0) {
          t = r.anchorNode;
          var l = r.anchorOffset, i = r.focusNode;
          r = r.focusOffset;
          try {
            t.nodeType, i.nodeType;
          } catch {
            t = null;
            break e;
          }
          var s = 0, d = -1, f = -1, g = 0, N = 0, E = e, j = null;
          n: for (; ; ) {
            for (var F; E !== t || l !== 0 && E.nodeType !== 3 || (d = s + l), E !== i || r !== 0 && E.nodeType !== 3 || (f = s + r), E.nodeType === 3 && (s += E.nodeValue.length), (F = E.firstChild) !== null; )
              j = E, E = F;
            for (; ; ) {
              if (E === e) break n;
              if (j === t && ++g === l && (d = s), j === i && ++N === r && (f = s), (F = E.nextSibling) !== null) break;
              E = j, j = E.parentNode;
            }
            E = F;
          }
          t = d === -1 || f === -1 ? null : { start: d, end: f };
        } else t = null;
      }
      t = t || { start: 0, end: 0 };
    } else t = null;
    for (Pi = { focusedElem: e, selectionRange: t }, qr = !1, M = n; M !== null; ) if (n = M, e = n.child, (n.subtreeFlags & 1028) !== 0 && e !== null) e.return = n, M = e;
    else for (; M !== null; ) {
      n = M;
      try {
        var I = n.alternate;
        if ((n.flags & 1024) !== 0) switch (n.tag) {
          case 0:
          case 11:
          case 15:
            break;
          case 1:
            if (I !== null) {
              var W = I.memoizedProps, je = I.memoizedState, m = n.stateNode, p = m.getSnapshotBeforeUpdate(n.elementType === n.type ? W : gn(n.type, W), je);
              m.__reactInternalSnapshotBeforeUpdate = p;
            }
            break;
          case 3:
            var v = n.stateNode.containerInfo;
            v.nodeType === 1 ? v.textContent = "" : v.nodeType === 9 && v.documentElement && v.removeChild(v.documentElement);
            break;
          case 5:
          case 6:
          case 4:
          case 17:
            break;
          default:
            throw Error(c(163));
        }
      } catch (C) {
        ke(n, n.return, C);
      }
      if (e = n.sibling, e !== null) {
        e.return = n.return, M = e;
        break;
      }
      M = n.return;
    }
    return I = ma, ma = !1, I;
  }
  function xr(e, n, t) {
    var r = n.updateQueue;
    if (r = r !== null ? r.lastEffect : null, r !== null) {
      var l = r = r.next;
      do {
        if ((l.tag & e) === e) {
          var i = l.destroy;
          l.destroy = void 0, i !== void 0 && go(n, t, i);
        }
        l = l.next;
      } while (l !== r);
    }
  }
  function kl(e, n) {
    if (n = n.updateQueue, n = n !== null ? n.lastEffect : null, n !== null) {
      var t = n = n.next;
      do {
        if ((t.tag & e) === e) {
          var r = t.create;
          t.destroy = r();
        }
        t = t.next;
      } while (t !== n);
    }
  }
  function yo(e) {
    var n = e.ref;
    if (n !== null) {
      var t = e.stateNode;
      switch (e.tag) {
        case 5:
          e = t;
          break;
        default:
          e = t;
      }
      typeof n == "function" ? n(e) : n.current = e;
    }
  }
  function va(e) {
    var n = e.alternate;
    n !== null && (e.alternate = null, va(n)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (n = e.stateNode, n !== null && (delete n[jn], delete n[ur], delete n[Fi], delete n[Cd], delete n[zd])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
  }
  function ga(e) {
    return e.tag === 5 || e.tag === 3 || e.tag === 4;
  }
  function ya(e) {
    e: for (; ; ) {
      for (; e.sibling === null; ) {
        if (e.return === null || ga(e.return)) return null;
        e = e.return;
      }
      for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18; ) {
        if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
        e.child.return = e, e = e.child;
      }
      if (!(e.flags & 2)) return e.stateNode;
    }
  }
  function xo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.nodeType === 8 ? t.parentNode.insertBefore(e, n) : t.insertBefore(e, n) : (t.nodeType === 8 ? (n = t.parentNode, n.insertBefore(e, t)) : (n = t, n.appendChild(e)), t = t._reactRootContainer, t != null || n.onclick !== null || (n.onclick = _r));
    else if (r !== 4 && (e = e.child, e !== null)) for (xo(e, n, t), e = e.sibling; e !== null; ) xo(e, n, t), e = e.sibling;
  }
  function wo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.insertBefore(e, n) : t.appendChild(e);
    else if (r !== 4 && (e = e.child, e !== null)) for (wo(e, n, t), e = e.sibling; e !== null; ) wo(e, n, t), e = e.sibling;
  }
  var Ie = null, yn = !1;
  function Kn(e, n, t) {
    for (t = t.child; t !== null; ) xa(e, n, t), t = t.sibling;
  }
  function xa(e, n, t) {
    if (Sn && typeof Sn.onCommitFiberUnmount == "function") try {
      Sn.onCommitFiberUnmount(Mr, t);
    } catch {
    }
    switch (t.tag) {
      case 5:
        Be || It(t, n);
      case 6:
        var r = Ie, l = yn;
        Ie = null, Kn(e, n, t), Ie = r, yn = l, Ie !== null && (yn ? (e = Ie, t = t.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(t) : e.removeChild(t)) : Ie.removeChild(t.stateNode));
        break;
      case 18:
        Ie !== null && (yn ? (e = Ie, t = t.stateNode, e.nodeType === 8 ? Oi(e.parentNode, t) : e.nodeType === 1 && Oi(e, t), bt(e)) : Oi(Ie, t.stateNode));
        break;
      case 4:
        r = Ie, l = yn, Ie = t.stateNode.containerInfo, yn = !0, Kn(e, n, t), Ie = r, yn = l;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        if (!Be && (r = t.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
          l = r = r.next;
          do {
            var i = l, s = i.destroy;
            i = i.tag, s !== void 0 && ((i & 2) !== 0 || (i & 4) !== 0) && go(t, n, s), l = l.next;
          } while (l !== r);
        }
        Kn(e, n, t);
        break;
      case 1:
        if (!Be && (It(t, n), r = t.stateNode, typeof r.componentWillUnmount == "function")) try {
          r.props = t.memoizedProps, r.state = t.memoizedState, r.componentWillUnmount();
        } catch (d) {
          ke(t, n, d);
        }
        Kn(e, n, t);
        break;
      case 21:
        Kn(e, n, t);
        break;
      case 22:
        t.mode & 1 ? (Be = (r = Be) || t.memoizedState !== null, Kn(e, n, t), Be = r) : Kn(e, n, t);
        break;
      default:
        Kn(e, n, t);
    }
  }
  function wa(e) {
    var n = e.updateQueue;
    if (n !== null) {
      e.updateQueue = null;
      var t = e.stateNode;
      t === null && (t = e.stateNode = new Bd()), n.forEach(function(r) {
        var l = $d.bind(null, e, r);
        t.has(r) || (t.add(r), r.then(l, l));
      });
    }
  }
  function xn(e, n) {
    var t = n.deletions;
    if (t !== null) for (var r = 0; r < t.length; r++) {
      var l = t[r];
      try {
        var i = e, s = n, d = s;
        e: for (; d !== null; ) {
          switch (d.tag) {
            case 5:
              Ie = d.stateNode, yn = !1;
              break e;
            case 3:
              Ie = d.stateNode.containerInfo, yn = !0;
              break e;
            case 4:
              Ie = d.stateNode.containerInfo, yn = !0;
              break e;
          }
          d = d.return;
        }
        if (Ie === null) throw Error(c(160));
        xa(i, s, l), Ie = null, yn = !1;
        var f = l.alternate;
        f !== null && (f.return = null), l.return = null;
      } catch (g) {
        ke(l, n, g);
      }
    }
    if (n.subtreeFlags & 12854) for (n = n.child; n !== null; ) ka(n, e), n = n.sibling;
  }
  function ka(e, n) {
    var t = e.alternate, r = e.flags;
    switch (e.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        if (xn(n, e), Cn(e), r & 4) {
          try {
            xr(3, e, e.return), kl(3, e);
          } catch (W) {
            ke(e, e.return, W);
          }
          try {
            xr(5, e, e.return);
          } catch (W) {
            ke(e, e.return, W);
          }
        }
        break;
      case 1:
        xn(n, e), Cn(e), r & 512 && t !== null && It(t, t.return);
        break;
      case 5:
        if (xn(n, e), Cn(e), r & 512 && t !== null && It(t, t.return), e.flags & 32) {
          var l = e.stateNode;
          try {
            qt(l, "");
          } catch (W) {
            ke(e, e.return, W);
          }
        }
        if (r & 4 && (l = e.stateNode, l != null)) {
          var i = e.memoizedProps, s = t !== null ? t.memoizedProps : i, d = e.type, f = e.updateQueue;
          if (e.updateQueue = null, f !== null) try {
            d === "input" && i.type === "radio" && i.name != null && Go(l, i), Yl(d, s);
            var g = Yl(d, i);
            for (s = 0; s < f.length; s += 2) {
              var N = f[s], E = f[s + 1];
              N === "style" ? rs(l, E) : N === "dangerouslySetInnerHTML" ? ns(l, E) : N === "children" ? qt(l, E) : pe(l, N, E, g);
            }
            switch (d) {
              case "input":
                Zl(l, i);
                break;
              case "textarea":
                _o(l, i);
                break;
              case "select":
                var j = l._wrapperState.wasMultiple;
                l._wrapperState.wasMultiple = !!i.multiple;
                var F = i.value;
                F != null ? ht(l, !!i.multiple, F, !1) : j !== !!i.multiple && (i.defaultValue != null ? ht(
                  l,
                  !!i.multiple,
                  i.defaultValue,
                  !0
                ) : ht(l, !!i.multiple, i.multiple ? [] : "", !1));
            }
            l[ur] = i;
          } catch (W) {
            ke(e, e.return, W);
          }
        }
        break;
      case 6:
        if (xn(n, e), Cn(e), r & 4) {
          if (e.stateNode === null) throw Error(c(162));
          l = e.stateNode, i = e.memoizedProps;
          try {
            l.nodeValue = i;
          } catch (W) {
            ke(e, e.return, W);
          }
        }
        break;
      case 3:
        if (xn(n, e), Cn(e), r & 4 && t !== null && t.memoizedState.isDehydrated) try {
          bt(n.containerInfo);
        } catch (W) {
          ke(e, e.return, W);
        }
        break;
      case 4:
        xn(n, e), Cn(e);
        break;
      case 13:
        xn(n, e), Cn(e), l = e.child, l.flags & 8192 && (i = l.memoizedState !== null, l.stateNode.isHidden = i, !i || l.alternate !== null && l.alternate.memoizedState !== null || (jo = Se())), r & 4 && wa(e);
        break;
      case 22:
        if (N = t !== null && t.memoizedState !== null, e.mode & 1 ? (Be = (g = Be) || N, xn(n, e), Be = g) : xn(n, e), Cn(e), r & 8192) {
          if (g = e.memoizedState !== null, (e.stateNode.isHidden = g) && !N && (e.mode & 1) !== 0) for (M = e, N = e.child; N !== null; ) {
            for (E = M = N; M !== null; ) {
              switch (j = M, F = j.child, j.tag) {
                case 0:
                case 11:
                case 14:
                case 15:
                  xr(4, j, j.return);
                  break;
                case 1:
                  It(j, j.return);
                  var I = j.stateNode;
                  if (typeof I.componentWillUnmount == "function") {
                    r = j, t = j.return;
                    try {
                      n = r, I.props = n.memoizedProps, I.state = n.memoizedState, I.componentWillUnmount();
                    } catch (W) {
                      ke(r, t, W);
                    }
                  }
                  break;
                case 5:
                  It(j, j.return);
                  break;
                case 22:
                  if (j.memoizedState !== null) {
                    Na(E);
                    continue;
                  }
              }
              F !== null ? (F.return = j, M = F) : Na(E);
            }
            N = N.sibling;
          }
          e: for (N = null, E = e; ; ) {
            if (E.tag === 5) {
              if (N === null) {
                N = E;
                try {
                  l = E.stateNode, g ? (i = l.style, typeof i.setProperty == "function" ? i.setProperty("display", "none", "important") : i.display = "none") : (d = E.stateNode, f = E.memoizedProps.style, s = f != null && f.hasOwnProperty("display") ? f.display : null, d.style.display = ts("display", s));
                } catch (W) {
                  ke(e, e.return, W);
                }
              }
            } else if (E.tag === 6) {
              if (N === null) try {
                E.stateNode.nodeValue = g ? "" : E.memoizedProps;
              } catch (W) {
                ke(e, e.return, W);
              }
            } else if ((E.tag !== 22 && E.tag !== 23 || E.memoizedState === null || E === e) && E.child !== null) {
              E.child.return = E, E = E.child;
              continue;
            }
            if (E === e) break e;
            for (; E.sibling === null; ) {
              if (E.return === null || E.return === e) break e;
              N === E && (N = null), E = E.return;
            }
            N === E && (N = null), E.sibling.return = E.return, E = E.sibling;
          }
        }
        break;
      case 19:
        xn(n, e), Cn(e), r & 4 && wa(e);
        break;
      case 21:
        break;
      default:
        xn(
          n,
          e
        ), Cn(e);
    }
  }
  function Cn(e) {
    var n = e.flags;
    if (n & 2) {
      try {
        e: {
          for (var t = e.return; t !== null; ) {
            if (ga(t)) {
              var r = t;
              break e;
            }
            t = t.return;
          }
          throw Error(c(160));
        }
        switch (r.tag) {
          case 5:
            var l = r.stateNode;
            r.flags & 32 && (qt(l, ""), r.flags &= -33);
            var i = ya(e);
            wo(e, i, l);
            break;
          case 3:
          case 4:
            var s = r.stateNode.containerInfo, d = ya(e);
            xo(e, d, s);
            break;
          default:
            throw Error(c(161));
        }
      } catch (f) {
        ke(e, e.return, f);
      }
      e.flags &= -3;
    }
    n & 4096 && (e.flags &= -4097);
  }
  function Zd(e, n, t) {
    M = e, Sa(e);
  }
  function Sa(e, n, t) {
    for (var r = (e.mode & 1) !== 0; M !== null; ) {
      var l = M, i = l.child;
      if (l.tag === 22 && r) {
        var s = l.memoizedState !== null || wl;
        if (!s) {
          var d = l.alternate, f = d !== null && d.memoizedState !== null || Be;
          d = wl;
          var g = Be;
          if (wl = s, (Be = f) && !g) for (M = l; M !== null; ) s = M, f = s.child, s.tag === 22 && s.memoizedState !== null ? Ea(l) : f !== null ? (f.return = s, M = f) : Ea(l);
          for (; i !== null; ) M = i, Sa(i), i = i.sibling;
          M = l, wl = d, Be = g;
        }
        ja(e);
      } else (l.subtreeFlags & 8772) !== 0 && i !== null ? (i.return = l, M = i) : ja(e);
    }
  }
  function ja(e) {
    for (; M !== null; ) {
      var n = M;
      if ((n.flags & 8772) !== 0) {
        var t = n.alternate;
        try {
          if ((n.flags & 8772) !== 0) switch (n.tag) {
            case 0:
            case 11:
            case 15:
              Be || kl(5, n);
              break;
            case 1:
              var r = n.stateNode;
              if (n.flags & 4 && !Be) if (t === null) r.componentDidMount();
              else {
                var l = n.elementType === n.type ? t.memoizedProps : gn(n.type, t.memoizedProps);
                r.componentDidUpdate(l, t.memoizedState, r.__reactInternalSnapshotBeforeUpdate);
              }
              var i = n.updateQueue;
              i !== null && Nu(n, i, r);
              break;
            case 3:
              var s = n.updateQueue;
              if (s !== null) {
                if (t = null, n.child !== null) switch (n.child.tag) {
                  case 5:
                    t = n.child.stateNode;
                    break;
                  case 1:
                    t = n.child.stateNode;
                }
                Nu(n, s, t);
              }
              break;
            case 5:
              var d = n.stateNode;
              if (t === null && n.flags & 4) {
                t = d;
                var f = n.memoizedProps;
                switch (n.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    f.autoFocus && t.focus();
                    break;
                  case "img":
                    f.src && (t.src = f.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (n.memoizedState === null) {
                var g = n.alternate;
                if (g !== null) {
                  var N = g.memoizedState;
                  if (N !== null) {
                    var E = N.dehydrated;
                    E !== null && bt(E);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(c(163));
          }
          Be || n.flags & 512 && yo(n);
        } catch (j) {
          ke(n, n.return, j);
        }
      }
      if (n === e) {
        M = null;
        break;
      }
      if (t = n.sibling, t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function Na(e) {
    for (; M !== null; ) {
      var n = M;
      if (n === e) {
        M = null;
        break;
      }
      var t = n.sibling;
      if (t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function Ea(e) {
    for (; M !== null; ) {
      var n = M;
      try {
        switch (n.tag) {
          case 0:
          case 11:
          case 15:
            var t = n.return;
            try {
              kl(4, n);
            } catch (f) {
              ke(n, t, f);
            }
            break;
          case 1:
            var r = n.stateNode;
            if (typeof r.componentDidMount == "function") {
              var l = n.return;
              try {
                r.componentDidMount();
              } catch (f) {
                ke(n, l, f);
              }
            }
            var i = n.return;
            try {
              yo(n);
            } catch (f) {
              ke(n, i, f);
            }
            break;
          case 5:
            var s = n.return;
            try {
              yo(n);
            } catch (f) {
              ke(n, s, f);
            }
        }
      } catch (f) {
        ke(n, n.return, f);
      }
      if (n === e) {
        M = null;
        break;
      }
      var d = n.sibling;
      if (d !== null) {
        d.return = n.return, M = d;
        break;
      }
      M = n.return;
    }
  }
  var Jd = Math.ceil, Sl = ge.ReactCurrentDispatcher, ko = ge.ReactCurrentOwner, fn = ge.ReactCurrentBatchConfig, _ = 0, Le = null, Ne = null, We = 0, on = 0, Wt = An(0), Re = 0, wr = null, at = 0, jl = 0, So = 0, kr = null, be = null, jo = 0, Dt = 1 / 0, Mn = null, Nl = !1, No = null, Qn = null, El = !1, Gn = null, Cl = 0, Sr = 0, Eo = null, zl = -1, Rl = 0;
  function Je() {
    return (_ & 6) !== 0 ? Se() : zl !== -1 ? zl : zl = Se();
  }
  function Yn(e) {
    return (e.mode & 1) === 0 ? 1 : (_ & 2) !== 0 && We !== 0 ? We & -We : Pd.transition !== null ? (Rl === 0 && (Rl = ys()), Rl) : (e = re, e !== 0 || (e = window.event, e = e === void 0 ? 16 : zs(e.type)), e);
  }
  function wn(e, n, t, r) {
    if (50 < Sr) throw Sr = 0, Eo = null, Error(c(185));
    Jt(e, t, r), ((_ & 2) === 0 || e !== Le) && (e === Le && ((_ & 2) === 0 && (jl |= t), Re === 4 && bn(e, We)), _e(e, r), t === 1 && _ === 0 && (n.mode & 1) === 0 && (Dt = Se() + 500, tl && Xn()));
  }
  function _e(e, n) {
    var t = e.callbackNode;
    Pc(e, n);
    var r = Dr(e, e === Le ? We : 0);
    if (r === 0) t !== null && ms(t), e.callbackNode = null, e.callbackPriority = 0;
    else if (n = r & -r, e.callbackPriority !== n) {
      if (t != null && ms(t), n === 1) e.tag === 0 ? Rd(za.bind(null, e)) : fu(za.bind(null, e)), Nd(function() {
        (_ & 6) === 0 && Xn();
      }), t = null;
      else {
        switch (xs(r)) {
          case 1:
            t = ri;
            break;
          case 4:
            t = vs;
            break;
          case 16:
            t = Fr;
            break;
          case 536870912:
            t = gs;
            break;
          default:
            t = Fr;
        }
        t = Ia(t, Ca.bind(null, e));
      }
      e.callbackPriority = n, e.callbackNode = t;
    }
  }
  function Ca(e, n) {
    if (zl = -1, Rl = 0, (_ & 6) !== 0) throw Error(c(327));
    var t = e.callbackNode;
    if (Vt() && e.callbackNode !== t) return null;
    var r = Dr(e, e === Le ? We : 0);
    if (r === 0) return null;
    if ((r & 30) !== 0 || (r & e.expiredLanes) !== 0 || n) n = Pl(e, r);
    else {
      n = r;
      var l = _;
      _ |= 2;
      var i = Pa();
      (Le !== e || We !== n) && (Mn = null, Dt = Se() + 500, dt(e, n));
      do
        try {
          Gd();
          break;
        } catch (d) {
          Ra(e, d);
        }
      while (!0);
      Ai(), Sl.current = i, _ = l, Ne !== null ? n = 0 : (Le = null, We = 0, n = Re);
    }
    if (n !== 0) {
      if (n === 2 && (l = li(e), l !== 0 && (r = l, n = Co(e, l))), n === 1) throw t = wr, dt(e, 0), bn(e, r), _e(e, Se()), t;
      if (n === 6) bn(e, r);
      else {
        if (l = e.current.alternate, (r & 30) === 0 && !Kd(l) && (n = Pl(e, r), n === 2 && (i = li(e), i !== 0 && (r = i, n = Co(e, i))), n === 1)) throw t = wr, dt(e, 0), bn(e, r), _e(e, Se()), t;
        switch (e.finishedWork = l, e.finishedLanes = r, n) {
          case 0:
          case 1:
            throw Error(c(345));
          case 2:
            ft(e, be, Mn);
            break;
          case 3:
            if (bn(e, r), (r & 130023424) === r && (n = jo + 500 - Se(), 10 < n)) {
              if (Dr(e, 0) !== 0) break;
              if (l = e.suspendedLanes, (l & r) !== r) {
                Je(), e.pingedLanes |= e.suspendedLanes & l;
                break;
              }
              e.timeoutHandle = Li(ft.bind(null, e, be, Mn), n);
              break;
            }
            ft(e, be, Mn);
            break;
          case 4:
            if (bn(e, r), (r & 4194240) === r) break;
            for (n = e.eventTimes, l = -1; 0 < r; ) {
              var s = 31 - hn(r);
              i = 1 << s, s = n[s], s > l && (l = s), r &= ~i;
            }
            if (r = l, r = Se() - r, r = (120 > r ? 120 : 480 > r ? 480 : 1080 > r ? 1080 : 1920 > r ? 1920 : 3e3 > r ? 3e3 : 4320 > r ? 4320 : 1960 * Jd(r / 1960)) - r, 10 < r) {
              e.timeoutHandle = Li(ft.bind(null, e, be, Mn), r);
              break;
            }
            ft(e, be, Mn);
            break;
          case 5:
            ft(e, be, Mn);
            break;
          default:
            throw Error(c(329));
        }
      }
    }
    return _e(e, Se()), e.callbackNode === t ? Ca.bind(null, e) : null;
  }
  function Co(e, n) {
    var t = kr;
    return e.current.memoizedState.isDehydrated && (dt(e, n).flags |= 256), e = Pl(e, n), e !== 2 && (n = be, be = t, n !== null && zo(n)), e;
  }
  function zo(e) {
    be === null ? be = e : be.push.apply(be, e);
  }
  function Kd(e) {
    for (var n = e; ; ) {
      if (n.flags & 16384) {
        var t = n.updateQueue;
        if (t !== null && (t = t.stores, t !== null)) for (var r = 0; r < t.length; r++) {
          var l = t[r], i = l.getSnapshot;
          l = l.value;
          try {
            if (!mn(i(), l)) return !1;
          } catch {
            return !1;
          }
        }
      }
      if (t = n.child, n.subtreeFlags & 16384 && t !== null) t.return = n, n = t;
      else {
        if (n === e) break;
        for (; n.sibling === null; ) {
          if (n.return === null || n.return === e) return !0;
          n = n.return;
        }
        n.sibling.return = n.return, n = n.sibling;
      }
    }
    return !0;
  }
  function bn(e, n) {
    for (n &= ~So, n &= ~jl, e.suspendedLanes |= n, e.pingedLanes &= ~n, e = e.expirationTimes; 0 < n; ) {
      var t = 31 - hn(n), r = 1 << t;
      e[t] = -1, n &= ~r;
    }
  }
  function za(e) {
    if ((_ & 6) !== 0) throw Error(c(327));
    Vt();
    var n = Dr(e, 0);
    if ((n & 1) === 0) return _e(e, Se()), null;
    var t = Pl(e, n);
    if (e.tag !== 0 && t === 2) {
      var r = li(e);
      r !== 0 && (n = r, t = Co(e, r));
    }
    if (t === 1) throw t = wr, dt(e, 0), bn(e, n), _e(e, Se()), t;
    if (t === 6) throw Error(c(345));
    return e.finishedWork = e.current.alternate, e.finishedLanes = n, ft(e, be, Mn), _e(e, Se()), null;
  }
  function Ro(e, n) {
    var t = _;
    _ |= 1;
    try {
      return e(n);
    } finally {
      _ = t, _ === 0 && (Dt = Se() + 500, tl && Xn());
    }
  }
  function ct(e) {
    Gn !== null && Gn.tag === 0 && (_ & 6) === 0 && Vt();
    var n = _;
    _ |= 1;
    var t = fn.transition, r = re;
    try {
      if (fn.transition = null, re = 1, e) return e();
    } finally {
      re = r, fn.transition = t, _ = n, (_ & 6) === 0 && Xn();
    }
  }
  function Po() {
    on = Wt.current, de(Wt);
  }
  function dt(e, n) {
    e.finishedWork = null, e.finishedLanes = 0;
    var t = e.timeoutHandle;
    if (t !== -1 && (e.timeoutHandle = -1, jd(t)), Ne !== null) for (t = Ne.return; t !== null; ) {
      var r = t;
      switch (Di(r), r.tag) {
        case 1:
          r = r.type.childContextTypes, r != null && el();
          break;
        case 3:
          Ft(), de(Qe), de(qe), Yi();
          break;
        case 5:
          Qi(r);
          break;
        case 4:
          Ft();
          break;
        case 13:
          de(ye);
          break;
        case 19:
          de(ye);
          break;
        case 10:
          Bi(r.type._context);
          break;
        case 22:
        case 23:
          Po();
      }
      t = t.return;
    }
    if (Le = e, Ne = e = _n(e.current, null), We = on = n, Re = 0, wr = null, So = jl = at = 0, be = kr = null, ot !== null) {
      for (n = 0; n < ot.length; n++) if (t = ot[n], r = t.interleaved, r !== null) {
        t.interleaved = null;
        var l = r.next, i = t.pending;
        if (i !== null) {
          var s = i.next;
          i.next = l, r.next = s;
        }
        t.pending = r;
      }
      ot = null;
    }
    return e;
  }
  function Ra(e, n) {
    do {
      var t = Ne;
      try {
        if (Ai(), fl.current = vl, pl) {
          for (var r = xe.memoizedState; r !== null; ) {
            var l = r.queue;
            l !== null && (l.pending = null), r = r.next;
          }
          pl = !1;
        }
        if (ut = 0, Te = ze = xe = null, hr = !1, mr = 0, ko.current = null, t === null || t.return === null) {
          Re = 1, wr = n, Ne = null;
          break;
        }
        e: {
          var i = e, s = t.return, d = t, f = n;
          if (n = We, d.flags |= 32768, f !== null && typeof f == "object" && typeof f.then == "function") {
            var g = f, N = d, E = N.tag;
            if ((N.mode & 1) === 0 && (E === 0 || E === 11 || E === 15)) {
              var j = N.alternate;
              j ? (N.updateQueue = j.updateQueue, N.memoizedState = j.memoizedState, N.lanes = j.lanes) : (N.updateQueue = null, N.memoizedState = null);
            }
            var F = $u(s);
            if (F !== null) {
              F.flags &= -257, ea(F, s, d, i, n), F.mode & 1 && _u(i, g, n), n = F, f = g;
              var I = n.updateQueue;
              if (I === null) {
                var W = /* @__PURE__ */ new Set();
                W.add(f), n.updateQueue = W;
              } else I.add(f);
              break e;
            } else {
              if ((n & 1) === 0) {
                _u(i, g, n), To();
                break e;
              }
              f = Error(c(426));
            }
          } else if (me && d.mode & 1) {
            var je = $u(s);
            if (je !== null) {
              (je.flags & 65536) === 0 && (je.flags |= 256), ea(je, s, d, i, n), qi(Mt(f, d));
              break e;
            }
          }
          i = f = Mt(f, d), Re !== 4 && (Re = 2), kr === null ? kr = [i] : kr.push(i), i = s;
          do {
            switch (i.tag) {
              case 3:
                i.flags |= 65536, n &= -n, i.lanes |= n;
                var m = Yu(i, f, n);
                ju(i, m);
                break e;
              case 1:
                d = f;
                var p = i.type, v = i.stateNode;
                if ((i.flags & 128) === 0 && (typeof p.getDerivedStateFromError == "function" || v !== null && typeof v.componentDidCatch == "function" && (Qn === null || !Qn.has(v)))) {
                  i.flags |= 65536, n &= -n, i.lanes |= n;
                  var C = bu(i, d, n);
                  ju(i, C);
                  break e;
                }
            }
            i = i.return;
          } while (i !== null);
        }
        La(t);
      } catch (D) {
        n = D, Ne === t && t !== null && (Ne = t = t.return);
        continue;
      }
      break;
    } while (!0);
  }
  function Pa() {
    var e = Sl.current;
    return Sl.current = vl, e === null ? vl : e;
  }
  function To() {
    (Re === 0 || Re === 3 || Re === 2) && (Re = 4), Le === null || (at & 268435455) === 0 && (jl & 268435455) === 0 || bn(Le, We);
  }
  function Pl(e, n) {
    var t = _;
    _ |= 2;
    var r = Pa();
    (Le !== e || We !== n) && (Mn = null, dt(e, n));
    do
      try {
        Qd();
        break;
      } catch (l) {
        Ra(e, l);
      }
    while (!0);
    if (Ai(), _ = t, Sl.current = r, Ne !== null) throw Error(c(261));
    return Le = null, We = 0, Re;
  }
  function Qd() {
    for (; Ne !== null; ) Ta(Ne);
  }
  function Gd() {
    for (; Ne !== null && !wc(); ) Ta(Ne);
  }
  function Ta(e) {
    var n = Ma(e.alternate, e, on);
    e.memoizedProps = e.pendingProps, n === null ? La(e) : Ne = n, ko.current = null;
  }
  function La(e) {
    var n = e;
    do {
      var t = n.alternate;
      if (e = n.return, (n.flags & 32768) === 0) {
        if (t = Hd(t, n, on), t !== null) {
          Ne = t;
          return;
        }
      } else {
        if (t = Ad(t, n), t !== null) {
          t.flags &= 32767, Ne = t;
          return;
        }
        if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
        else {
          Re = 6, Ne = null;
          return;
        }
      }
      if (n = n.sibling, n !== null) {
        Ne = n;
        return;
      }
      Ne = n = e;
    } while (n !== null);
    Re === 0 && (Re = 5);
  }
  function ft(e, n, t) {
    var r = re, l = fn.transition;
    try {
      fn.transition = null, re = 1, Yd(e, n, t, r);
    } finally {
      fn.transition = l, re = r;
    }
    return null;
  }
  function Yd(e, n, t, r) {
    do
      Vt();
    while (Gn !== null);
    if ((_ & 6) !== 0) throw Error(c(327));
    t = e.finishedWork;
    var l = e.finishedLanes;
    if (t === null) return null;
    if (e.finishedWork = null, e.finishedLanes = 0, t === e.current) throw Error(c(177));
    e.callbackNode = null, e.callbackPriority = 0;
    var i = t.lanes | t.childLanes;
    if (Tc(e, i), e === Le && (Ne = Le = null, We = 0), (t.subtreeFlags & 2064) === 0 && (t.flags & 2064) === 0 || El || (El = !0, Ia(Fr, function() {
      return Vt(), null;
    })), i = (t.flags & 15990) !== 0, (t.subtreeFlags & 15990) !== 0 || i) {
      i = fn.transition, fn.transition = null;
      var s = re;
      re = 1;
      var d = _;
      _ |= 4, ko.current = null, Xd(e, t), ka(t, e), vd(Pi), qr = !!Ri, Pi = Ri = null, e.current = t, Zd(t), kc(), _ = d, re = s, fn.transition = i;
    } else e.current = t;
    if (El && (El = !1, Gn = e, Cl = l), i = e.pendingLanes, i === 0 && (Qn = null), Nc(t.stateNode), _e(e, Se()), n !== null) for (r = e.onRecoverableError, t = 0; t < n.length; t++) l = n[t], r(l.value, { componentStack: l.stack, digest: l.digest });
    if (Nl) throw Nl = !1, e = No, No = null, e;
    return (Cl & 1) !== 0 && e.tag !== 0 && Vt(), i = e.pendingLanes, (i & 1) !== 0 ? e === Eo ? Sr++ : (Sr = 0, Eo = e) : Sr = 0, Xn(), null;
  }
  function Vt() {
    if (Gn !== null) {
      var e = xs(Cl), n = fn.transition, t = re;
      try {
        if (fn.transition = null, re = 16 > e ? 16 : e, Gn === null) var r = !1;
        else {
          if (e = Gn, Gn = null, Cl = 0, (_ & 6) !== 0) throw Error(c(331));
          var l = _;
          for (_ |= 4, M = e.current; M !== null; ) {
            var i = M, s = i.child;
            if ((M.flags & 16) !== 0) {
              var d = i.deletions;
              if (d !== null) {
                for (var f = 0; f < d.length; f++) {
                  var g = d[f];
                  for (M = g; M !== null; ) {
                    var N = M;
                    switch (N.tag) {
                      case 0:
                      case 11:
                      case 15:
                        xr(8, N, i);
                    }
                    var E = N.child;
                    if (E !== null) E.return = N, M = E;
                    else for (; M !== null; ) {
                      N = M;
                      var j = N.sibling, F = N.return;
                      if (va(N), N === g) {
                        M = null;
                        break;
                      }
                      if (j !== null) {
                        j.return = F, M = j;
                        break;
                      }
                      M = F;
                    }
                  }
                }
                var I = i.alternate;
                if (I !== null) {
                  var W = I.child;
                  if (W !== null) {
                    I.child = null;
                    do {
                      var je = W.sibling;
                      W.sibling = null, W = je;
                    } while (W !== null);
                  }
                }
                M = i;
              }
            }
            if ((i.subtreeFlags & 2064) !== 0 && s !== null) s.return = i, M = s;
            else e: for (; M !== null; ) {
              if (i = M, (i.flags & 2048) !== 0) switch (i.tag) {
                case 0:
                case 11:
                case 15:
                  xr(9, i, i.return);
              }
              var m = i.sibling;
              if (m !== null) {
                m.return = i.return, M = m;
                break e;
              }
              M = i.return;
            }
          }
          var p = e.current;
          for (M = p; M !== null; ) {
            s = M;
            var v = s.child;
            if ((s.subtreeFlags & 2064) !== 0 && v !== null) v.return = s, M = v;
            else e: for (s = p; M !== null; ) {
              if (d = M, (d.flags & 2048) !== 0) try {
                switch (d.tag) {
                  case 0:
                  case 11:
                  case 15:
                    kl(9, d);
                }
              } catch (D) {
                ke(d, d.return, D);
              }
              if (d === s) {
                M = null;
                break e;
              }
              var C = d.sibling;
              if (C !== null) {
                C.return = d.return, M = C;
                break e;
              }
              M = d.return;
            }
          }
          if (_ = l, Xn(), Sn && typeof Sn.onPostCommitFiberRoot == "function") try {
            Sn.onPostCommitFiberRoot(Mr, e);
          } catch {
          }
          r = !0;
        }
        return r;
      } finally {
        re = t, fn.transition = n;
      }
    }
    return !1;
  }
  function Oa(e, n, t) {
    n = Mt(t, n), n = Yu(e, n, 1), e = Jn(e, n, 1), n = Je(), e !== null && (Jt(e, 1, n), _e(e, n));
  }
  function ke(e, n, t) {
    if (e.tag === 3) Oa(e, e, t);
    else for (; n !== null; ) {
      if (n.tag === 3) {
        Oa(n, e, t);
        break;
      } else if (n.tag === 1) {
        var r = n.stateNode;
        if (typeof n.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (Qn === null || !Qn.has(r))) {
          e = Mt(t, e), e = bu(n, e, 1), n = Jn(n, e, 1), e = Je(), n !== null && (Jt(n, 1, e), _e(n, e));
          break;
        }
      }
      n = n.return;
    }
  }
  function bd(e, n, t) {
    var r = e.pingCache;
    r !== null && r.delete(n), n = Je(), e.pingedLanes |= e.suspendedLanes & t, Le === e && (We & t) === t && (Re === 4 || Re === 3 && (We & 130023424) === We && 500 > Se() - jo ? dt(e, 0) : So |= t), _e(e, n);
  }
  function Fa(e, n) {
    n === 0 && ((e.mode & 1) === 0 ? n = 1 : (n = Wr, Wr <<= 1, (Wr & 130023424) === 0 && (Wr = 4194304)));
    var t = Je();
    e = Ln(e, n), e !== null && (Jt(e, n, t), _e(e, t));
  }
  function _d(e) {
    var n = e.memoizedState, t = 0;
    n !== null && (t = n.retryLane), Fa(e, t);
  }
  function $d(e, n) {
    var t = 0;
    switch (e.tag) {
      case 13:
        var r = e.stateNode, l = e.memoizedState;
        l !== null && (t = l.retryLane);
        break;
      case 19:
        r = e.stateNode;
        break;
      default:
        throw Error(c(314));
    }
    r !== null && r.delete(n), Fa(e, t);
  }
  var Ma;
  Ma = function(e, n, t) {
    if (e !== null) if (e.memoizedProps !== n.pendingProps || Qe.current) Ye = !0;
    else {
      if ((e.lanes & t) === 0 && (n.flags & 128) === 0) return Ye = !1, qd(e, n, t);
      Ye = (e.flags & 131072) !== 0;
    }
    else Ye = !1, me && (n.flags & 1048576) !== 0 && pu(n, ll, n.index);
    switch (n.lanes = 0, n.tag) {
      case 2:
        var r = n.type;
        xl(e, n), e = n.pendingProps;
        var l = Ct(n, qe.current);
        Ot(n, t), l = $i(null, n, r, e, l, t);
        var i = eo();
        return n.flags |= 1, typeof l == "object" && l !== null && typeof l.render == "function" && l.$$typeof === void 0 ? (n.tag = 1, n.memoizedState = null, n.updateQueue = null, Ge(r) ? (i = !0, nl(n)) : i = !1, n.memoizedState = l.state !== null && l.state !== void 0 ? l.state : null, Ji(n), l.updater = gl, n.stateNode = l, l._reactInternals = n, oo(n, r, e, t), n = co(null, n, r, !0, i, t)) : (n.tag = 0, me && i && Wi(n), Ze(null, n, l, t), n = n.child), n;
      case 16:
        r = n.elementType;
        e: {
          switch (xl(e, n), e = n.pendingProps, l = r._init, r = l(r._payload), n.type = r, l = n.tag = nf(r), e = gn(r, e), l) {
            case 0:
              n = ao(null, n, r, e, t);
              break e;
            case 1:
              n = oa(null, n, r, e, t);
              break e;
            case 11:
              n = na(null, n, r, e, t);
              break e;
            case 14:
              n = ta(null, n, r, gn(r.type, e), t);
              break e;
          }
          throw Error(c(
            306,
            r,
            ""
          ));
        }
        return n;
      case 0:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), ao(e, n, r, l, t);
      case 1:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), oa(e, n, r, l, t);
      case 3:
        e: {
          if (sa(n), e === null) throw Error(c(387));
          r = n.pendingProps, i = n.memoizedState, l = i.element, Su(e, n), cl(n, r, null, t);
          var s = n.memoizedState;
          if (r = s.element, i.isDehydrated) if (i = { element: r, isDehydrated: !1, cache: s.cache, pendingSuspenseBoundaries: s.pendingSuspenseBoundaries, transitions: s.transitions }, n.updateQueue.baseState = i, n.memoizedState = i, n.flags & 256) {
            l = Mt(Error(c(423)), n), n = ua(e, n, r, t, l);
            break e;
          } else if (r !== l) {
            l = Mt(Error(c(424)), n), n = ua(e, n, r, t, l);
            break e;
          } else for (ln = Hn(n.stateNode.containerInfo.firstChild), rn = n, me = !0, vn = null, t = wu(n, null, r, t), n.child = t; t; ) t.flags = t.flags & -3 | 4096, t = t.sibling;
          else {
            if (Pt(), r === l) {
              n = Fn(e, n, t);
              break e;
            }
            Ze(e, n, r, t);
          }
          n = n.child;
        }
        return n;
      case 5:
        return Eu(n), e === null && Ui(n), r = n.type, l = n.pendingProps, i = e !== null ? e.memoizedProps : null, s = l.children, Ti(r, l) ? s = null : i !== null && Ti(r, i) && (n.flags |= 32), ia(e, n), Ze(e, n, s, t), n.child;
      case 6:
        return e === null && Ui(n), null;
      case 13:
        return aa(e, n, t);
      case 4:
        return Ki(n, n.stateNode.containerInfo), r = n.pendingProps, e === null ? n.child = Tt(n, null, r, t) : Ze(e, n, r, t), n.child;
      case 11:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), na(e, n, r, l, t);
      case 7:
        return Ze(e, n, n.pendingProps, t), n.child;
      case 8:
        return Ze(e, n, n.pendingProps.children, t), n.child;
      case 12:
        return Ze(e, n, n.pendingProps.children, t), n.child;
      case 10:
        e: {
          if (r = n.type._context, l = n.pendingProps, i = n.memoizedProps, s = l.value, ue(sl, r._currentValue), r._currentValue = s, i !== null) if (mn(i.value, s)) {
            if (i.children === l.children && !Qe.current) {
              n = Fn(e, n, t);
              break e;
            }
          } else for (i = n.child, i !== null && (i.return = n); i !== null; ) {
            var d = i.dependencies;
            if (d !== null) {
              s = i.child;
              for (var f = d.firstContext; f !== null; ) {
                if (f.context === r) {
                  if (i.tag === 1) {
                    f = On(-1, t & -t), f.tag = 2;
                    var g = i.updateQueue;
                    if (g !== null) {
                      g = g.shared;
                      var N = g.pending;
                      N === null ? f.next = f : (f.next = N.next, N.next = f), g.pending = f;
                    }
                  }
                  i.lanes |= t, f = i.alternate, f !== null && (f.lanes |= t), Xi(
                    i.return,
                    t,
                    n
                  ), d.lanes |= t;
                  break;
                }
                f = f.next;
              }
            } else if (i.tag === 10) s = i.type === n.type ? null : i.child;
            else if (i.tag === 18) {
              if (s = i.return, s === null) throw Error(c(341));
              s.lanes |= t, d = s.alternate, d !== null && (d.lanes |= t), Xi(s, t, n), s = i.sibling;
            } else s = i.child;
            if (s !== null) s.return = i;
            else for (s = i; s !== null; ) {
              if (s === n) {
                s = null;
                break;
              }
              if (i = s.sibling, i !== null) {
                i.return = s.return, s = i;
                break;
              }
              s = s.return;
            }
            i = s;
          }
          Ze(e, n, l.children, t), n = n.child;
        }
        return n;
      case 9:
        return l = n.type, r = n.pendingProps.children, Ot(n, t), l = cn(l), r = r(l), n.flags |= 1, Ze(e, n, r, t), n.child;
      case 14:
        return r = n.type, l = gn(r, n.pendingProps), l = gn(r.type, l), ta(e, n, r, l, t);
      case 15:
        return ra(e, n, n.type, n.pendingProps, t);
      case 17:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), xl(e, n), n.tag = 1, Ge(r) ? (e = !0, nl(n)) : e = !1, Ot(n, t), Qu(n, r, l), oo(n, r, l, t), co(null, n, r, !0, e, t);
      case 19:
        return da(e, n, t);
      case 22:
        return la(e, n, t);
    }
    throw Error(c(156, n.tag));
  };
  function Ia(e, n) {
    return hs(e, n);
  }
  function ef(e, n, t, r) {
    this.tag = e, this.key = t, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = n, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function pn(e, n, t, r) {
    return new ef(e, n, t, r);
  }
  function Lo(e) {
    return e = e.prototype, !(!e || !e.isReactComponent);
  }
  function nf(e) {
    if (typeof e == "function") return Lo(e) ? 1 : 0;
    if (e != null) {
      if (e = e.$$typeof, e === V) return 11;
      if (e === Ue) return 14;
    }
    return 2;
  }
  function _n(e, n) {
    var t = e.alternate;
    return t === null ? (t = pn(e.tag, n, e.key, e.mode), t.elementType = e.elementType, t.type = e.type, t.stateNode = e.stateNode, t.alternate = e, e.alternate = t) : (t.pendingProps = n, t.type = e.type, t.flags = 0, t.subtreeFlags = 0, t.deletions = null), t.flags = e.flags & 14680064, t.childLanes = e.childLanes, t.lanes = e.lanes, t.child = e.child, t.memoizedProps = e.memoizedProps, t.memoizedState = e.memoizedState, t.updateQueue = e.updateQueue, n = e.dependencies, t.dependencies = n === null ? null : { lanes: n.lanes, firstContext: n.firstContext }, t.sibling = e.sibling, t.index = e.index, t.ref = e.ref, t;
  }
  function Tl(e, n, t, r, l, i) {
    var s = 2;
    if (r = e, typeof e == "function") Lo(e) && (s = 1);
    else if (typeof e == "string") s = 5;
    else e: switch (e) {
      case G:
        return pt(t.children, l, i, n);
      case oe:
        s = 8, l |= 8;
        break;
      case Xe:
        return e = pn(12, t, n, l | 2), e.elementType = Xe, e.lanes = i, e;
      case b:
        return e = pn(13, t, n, l), e.elementType = b, e.lanes = i, e;
      case Ce:
        return e = pn(19, t, n, l), e.elementType = Ce, e.lanes = i, e;
      case ae:
        return Ll(t, l, i, n);
      default:
        if (typeof e == "object" && e !== null) switch (e.$$typeof) {
          case Fe:
            s = 10;
            break e;
          case Ve:
            s = 9;
            break e;
          case V:
            s = 11;
            break e;
          case Ue:
            s = 14;
            break e;
          case Me:
            s = 16, r = null;
            break e;
        }
        throw Error(c(130, e == null ? e : typeof e, ""));
    }
    return n = pn(s, t, n, l), n.elementType = e, n.type = r, n.lanes = i, n;
  }
  function pt(e, n, t, r) {
    return e = pn(7, e, r, n), e.lanes = t, e;
  }
  function Ll(e, n, t, r) {
    return e = pn(22, e, r, n), e.elementType = ae, e.lanes = t, e.stateNode = { isHidden: !1 }, e;
  }
  function Oo(e, n, t) {
    return e = pn(6, e, null, n), e.lanes = t, e;
  }
  function Fo(e, n, t) {
    return n = pn(4, e.children !== null ? e.children : [], e.key, n), n.lanes = t, n.stateNode = { containerInfo: e.containerInfo, pendingChildren: null, implementation: e.implementation }, n;
  }
  function tf(e, n, t, r, l) {
    this.tag = n, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = ii(0), this.expirationTimes = ii(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = ii(0), this.identifierPrefix = r, this.onRecoverableError = l, this.mutableSourceEagerHydrationData = null;
  }
  function Mo(e, n, t, r, l, i, s, d, f) {
    return e = new tf(e, n, t, d, f), n === 1 ? (n = 1, i === !0 && (n |= 8)) : n = 0, i = pn(3, null, null, n), e.current = i, i.stateNode = e, i.memoizedState = { element: r, isDehydrated: t, cache: null, transitions: null, pendingSuspenseBoundaries: null }, Ji(i), e;
  }
  function rf(e, n, t) {
    var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return { $$typeof: we, key: r == null ? null : "" + r, children: e, containerInfo: n, implementation: t };
  }
  function Wa(e) {
    if (!e) return Bn;
    e = e._reactInternals;
    e: {
      if (nt(e) !== e || e.tag !== 1) throw Error(c(170));
      var n = e;
      do {
        switch (n.tag) {
          case 3:
            n = n.stateNode.context;
            break e;
          case 1:
            if (Ge(n.type)) {
              n = n.stateNode.__reactInternalMemoizedMergedChildContext;
              break e;
            }
        }
        n = n.return;
      } while (n !== null);
      throw Error(c(171));
    }
    if (e.tag === 1) {
      var t = e.type;
      if (Ge(t)) return cu(e, t, n);
    }
    return n;
  }
  function Da(e, n, t, r, l, i, s, d, f) {
    return e = Mo(t, r, !0, e, l, i, s, d, f), e.context = Wa(null), t = e.current, r = Je(), l = Yn(t), i = On(r, l), i.callback = n ?? null, Jn(t, i, l), e.current.lanes = l, Jt(e, l, r), _e(e, r), e;
  }
  function Ol(e, n, t, r) {
    var l = n.current, i = Je(), s = Yn(l);
    return t = Wa(t), n.context === null ? n.context = t : n.pendingContext = t, n = On(i, s), n.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (n.callback = r), e = Jn(l, n, s), e !== null && (wn(e, l, s, i), al(e, l, s)), s;
  }
  function Fl(e) {
    if (e = e.current, !e.child) return null;
    switch (e.child.tag) {
      case 5:
        return e.child.stateNode;
      default:
        return e.child.stateNode;
    }
  }
  function Va(e, n) {
    if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
      var t = e.retryLane;
      e.retryLane = t !== 0 && t < n ? t : n;
    }
  }
  function Io(e, n) {
    Va(e, n), (e = e.alternate) && Va(e, n);
  }
  function lf() {
    return null;
  }
  var Ua = typeof reportError == "function" ? reportError : function(e) {
    console.error(e);
  };
  function Wo(e) {
    this._internalRoot = e;
  }
  Ml.prototype.render = Wo.prototype.render = function(e) {
    var n = this._internalRoot;
    if (n === null) throw Error(c(409));
    Ol(e, n, null, null);
  }, Ml.prototype.unmount = Wo.prototype.unmount = function() {
    var e = this._internalRoot;
    if (e !== null) {
      this._internalRoot = null;
      var n = e.containerInfo;
      ct(function() {
        Ol(null, e, null, null);
      }), n[zn] = null;
    }
  };
  function Ml(e) {
    this._internalRoot = e;
  }
  Ml.prototype.unstable_scheduleHydration = function(e) {
    if (e) {
      var n = Ss();
      e = { blockedOn: null, target: e, priority: n };
      for (var t = 0; t < Vn.length && n !== 0 && n < Vn[t].priority; t++) ;
      Vn.splice(t, 0, e), t === 0 && Es(e);
    }
  };
  function Do(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
  }
  function Il(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
  }
  function qa() {
  }
  function of(e, n, t, r, l) {
    if (l) {
      if (typeof r == "function") {
        var i = r;
        r = function() {
          var g = Fl(s);
          i.call(g);
        };
      }
      var s = Da(n, r, e, 0, null, !1, !1, "", qa);
      return e._reactRootContainer = s, e[zn] = s.current, or(e.nodeType === 8 ? e.parentNode : e), ct(), s;
    }
    for (; l = e.lastChild; ) e.removeChild(l);
    if (typeof r == "function") {
      var d = r;
      r = function() {
        var g = Fl(f);
        d.call(g);
      };
    }
    var f = Mo(e, 0, !1, null, null, !1, !1, "", qa);
    return e._reactRootContainer = f, e[zn] = f.current, or(e.nodeType === 8 ? e.parentNode : e), ct(function() {
      Ol(n, f, t, r);
    }), f;
  }
  function Wl(e, n, t, r, l) {
    var i = t._reactRootContainer;
    if (i) {
      var s = i;
      if (typeof l == "function") {
        var d = l;
        l = function() {
          var f = Fl(s);
          d.call(f);
        };
      }
      Ol(n, s, e, l);
    } else s = of(t, n, e, l, r);
    return Fl(s);
  }
  ws = function(e) {
    switch (e.tag) {
      case 3:
        var n = e.stateNode;
        if (n.current.memoizedState.isDehydrated) {
          var t = Zt(n.pendingLanes);
          t !== 0 && (oi(n, t | 1), _e(n, Se()), (_ & 6) === 0 && (Dt = Se() + 500, Xn()));
        }
        break;
      case 13:
        ct(function() {
          var r = Ln(e, 1);
          if (r !== null) {
            var l = Je();
            wn(r, e, 1, l);
          }
        }), Io(e, 1);
    }
  }, si = function(e) {
    if (e.tag === 13) {
      var n = Ln(e, 134217728);
      if (n !== null) {
        var t = Je();
        wn(n, e, 134217728, t);
      }
      Io(e, 134217728);
    }
  }, ks = function(e) {
    if (e.tag === 13) {
      var n = Yn(e), t = Ln(e, n);
      if (t !== null) {
        var r = Je();
        wn(t, e, n, r);
      }
      Io(e, n);
    }
  }, Ss = function() {
    return re;
  }, js = function(e, n) {
    var t = re;
    try {
      return re = e, n();
    } finally {
      re = t;
    }
  }, $l = function(e, n, t) {
    switch (n) {
      case "input":
        if (Zl(e, t), n = t.name, t.type === "radio" && n != null) {
          for (t = e; t.parentNode; ) t = t.parentNode;
          for (t = t.querySelectorAll("input[name=" + JSON.stringify("" + n) + '][type="radio"]'), n = 0; n < t.length; n++) {
            var r = t[n];
            if (r !== e && r.form === e.form) {
              var l = $r(r);
              if (!l) throw Error(c(90));
              Ko(r), Zl(r, l);
            }
          }
        }
        break;
      case "textarea":
        _o(e, t);
        break;
      case "select":
        n = t.value, n != null && ht(e, !!t.multiple, n, !1);
    }
  }, ss = Ro, us = ct;
  var sf = { usingClientEntryPoint: !1, Events: [ar, Nt, $r, is, os, Ro] }, jr = { findFiberByHostInstance: tt, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, uf = { bundleType: jr.bundleType, version: jr.version, rendererPackageName: jr.rendererPackageName, rendererConfig: jr.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: ge.ReactCurrentDispatcher, findHostInstanceByFiber: function(e) {
    return e = fs(e), e === null ? null : e.stateNode;
  }, findFiberByHostInstance: jr.findFiberByHostInstance || lf, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var Dl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!Dl.isDisabled && Dl.supportsFiber) try {
      Mr = Dl.inject(uf), Sn = Dl;
    } catch {
    }
  }
  return $e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = sf, $e.createPortal = function(e, n) {
    var t = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!Do(n)) throw Error(c(200));
    return rf(e, n, null, t);
  }, $e.createRoot = function(e, n) {
    if (!Do(e)) throw Error(c(299));
    var t = !1, r = "", l = Ua;
    return n != null && (n.unstable_strictMode === !0 && (t = !0), n.identifierPrefix !== void 0 && (r = n.identifierPrefix), n.onRecoverableError !== void 0 && (l = n.onRecoverableError)), n = Mo(e, 1, !1, null, null, t, !1, r, l), e[zn] = n.current, or(e.nodeType === 8 ? e.parentNode : e), new Wo(n);
  }, $e.findDOMNode = function(e) {
    if (e == null) return null;
    if (e.nodeType === 1) return e;
    var n = e._reactInternals;
    if (n === void 0)
      throw typeof e.render == "function" ? Error(c(188)) : (e = Object.keys(e).join(","), Error(c(268, e)));
    return e = fs(n), e = e === null ? null : e.stateNode, e;
  }, $e.flushSync = function(e) {
    return ct(e);
  }, $e.hydrate = function(e, n, t) {
    if (!Il(n)) throw Error(c(200));
    return Wl(null, e, n, !0, t);
  }, $e.hydrateRoot = function(e, n, t) {
    if (!Do(e)) throw Error(c(405));
    var r = t != null && t.hydratedSources || null, l = !1, i = "", s = Ua;
    if (t != null && (t.unstable_strictMode === !0 && (l = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (s = t.onRecoverableError)), n = Da(n, null, e, 1, t ?? null, l, !1, i, s), e[zn] = n.current, or(e), r) for (e = 0; e < r.length; e++) t = r[e], l = t._getVersion, l = l(t._source), n.mutableSourceEagerHydrationData == null ? n.mutableSourceEagerHydrationData = [t, l] : n.mutableSourceEagerHydrationData.push(
      t,
      l
    );
    return new Ml(n);
  }, $e.render = function(e, n, t) {
    if (!Il(n)) throw Error(c(200));
    return Wl(null, e, n, !1, t);
  }, $e.unmountComponentAtNode = function(e) {
    if (!Il(e)) throw Error(c(40));
    return e._reactRootContainer ? (ct(function() {
      Wl(null, null, e, !1, function() {
        e._reactRootContainer = null, e[zn] = null;
      });
    }), !0) : !1;
  }, $e.unstable_batchedUpdates = Ro, $e.unstable_renderSubtreeIntoContainer = function(e, n, t, r) {
    if (!Il(t)) throw Error(c(200));
    if (e == null || e._reactInternals === void 0) throw Error(c(38));
    return Wl(e, n, t, !1, r);
  }, $e.version = "18.3.1-next-f1338f8080-20240426", $e;
}
var Qa;
function vf() {
  if (Qa) return qo.exports;
  Qa = 1;
  function u() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(u);
      } catch (a) {
        console.error(a);
      }
  }
  return u(), qo.exports = mf(), qo.exports;
}
var Ga;
function gf() {
  if (Ga) return Vl;
  Ga = 1;
  var u = vf();
  return Vl.createRoot = u.createRoot, Vl.hydrateRoot = u.hydrateRoot, Vl;
}
var yf = gf();
const xf = "data:image/png;base64,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", wf = "" + new URL("NotoColorEmoji-nature-Rpfd13Si.woff2", import.meta.url).href, kf = "" + new URL("NotoColorEmoji-objects-EKxheXEn.woff2", import.meta.url).href, Sf = { sans: 'Manrope, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Avenir Next", "Segoe UI", sans-serif', mono: '"IBM Plex Mono", "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace' }, jf = { eyebrow: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, sectionLabel: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, pageTitle: { size: "1.375rem", weight: 650, lineHeight: "1.2", tracking: "-0.02em" }, subtitle: { size: "0.8125rem", weight: 450, lineHeight: "1.45", tracking: "0" }, body: { size: "0.9375rem", weight: 400, lineHeight: "1.6", tracking: "0" }, input: { size: "0.875rem", weight: 450, lineHeight: "1.5", tracking: "0" }, mono: { size: "0.75rem", weight: 600, lineHeight: "1.4", tracking: "0" }, scoreValue: { size: "1.25rem", weight: 600, lineHeight: "1", tracking: "-0.02em" }, scoreLabel: { size: "0.625rem", weight: 650, lineHeight: "1", tracking: "0.08em" }, footer: { size: "0.6875rem", weight: 450, lineHeight: "1.4", tracking: "0" } }, Nf = { card: "12px", input: "10px", panel: "16px", pill: "999px" }, Ef = { duration: { fast: "120ms", mid: "200ms", slow: "420ms" }, easing: { standard: "cubic-bezier(.2, .8, .2, 1)", entrance: "cubic-bezier(.22, .8, .2, 1)" } }, Cf = { light: { washLow: "#FCEFD4", washHigh: "#F5B3A6", lineLow: "#E8A13C", lineHigh: "#D64540", safe: "#0E9384" }, dark: { washLow: "#4A3A1E", washHigh: "#4E2A26", lineLow: "#E0A24A", lineHigh: "#E8756B", safe: "#5FD6C6" } }, zf = { light: { colorScheme: "light", canvas: "#FAF3F8", card: "#FFFFFF", surface: "rgba(255, 255, 255, 0.92)", surface2: "rgba(255, 255, 255, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(250, 243, 248, 0.78), rgba(250, 243, 248, 0.30) 82%)", ink: "#231A21", muted: "#6B5F68", faint: "#A395A0", line: "#F0DFEA", lineStrong: "#E2C8D8", brand: "#E562A8", brandBright: "#EF7CB8", brandWash: "#FBE7F2", safe: "#0E9384", safeWash: "#D7F0EB", warning: "#81520C", warningWash: "#FCEFD4", riskInk: "#D64540", riskWash: "#F8DDD7", focus: "#1B6ED1", link: "#0E9384", mint: "#AFDEDD", shadowColor: "rgba(65, 45, 61, 0.14)", shadowCard: "0 1px 2px rgba(16, 24, 40, 0.04)", shadowRaised: "0 22px 62px rgba(69, 37, 57, 0.12)", sidebarBg: "rgba(255, 255, 255, 0.92)", inputBg: "rgba(255, 255, 255, 0.96)", popoverBg: "rgba(255, 255, 255, 0.98)", optionHover: "rgba(229, 98, 168, 0.16)", btnBg: "rgba(229, 98, 168, 0.10)", btnHoverBg: "rgba(229, 98, 168, 0.20)", btnHoverBorder: "rgba(229, 98, 168, 0.50)", pillBg: "rgba(255, 255, 255, 0.70)", pillSelected: "linear-gradient(135deg, rgba(229, 98, 168, 0.22), rgba(14, 147, 132, 0.16))", pillSelectedBorder: "rgba(229, 98, 168, 0.55)", scrollThumb: "rgba(229, 98, 168, 0.50)", scrollThumb2: "rgba(229, 98, 168, 0.42)", scrollThumbHover: "rgba(229, 98, 168, 0.66)" }, dark: { colorScheme: "dark", canvas: "#151116", card: "#211A22", surface: "rgba(33, 26, 34, 0.92)", surface2: "rgba(33, 26, 34, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(18, 13, 20, 0.50), rgba(18, 13, 20, 0.10) 82%)", ink: "#F9F5F7", muted: "#B9ADB5", faint: "#8E8089", line: "rgba(255, 231, 242, 0.15)", lineStrong: "rgba(255, 231, 242, 0.26)", brand: "#F07EBB", brandBright: "#F79BCB", brandWash: "#4D2034", safe: "#5FD6C6", safeWash: "#173B37", warning: "#F0BE6D", warningWash: "#422F17", riskInk: "#FF9499", riskWash: "#4E2428", focus: "#6CAEFF", link: "#7FD8CA", mint: "#AFDEDD", shadowColor: "rgba(0, 0, 0, 0.50)", shadowCard: "0 1px 2px rgba(0, 0, 0, 0.30)", shadowRaised: "0 24px 70px rgba(0, 0, 0, 0.32)", sidebarBg: "rgba(21, 17, 22, 0.93)", inputBg: "rgba(20, 16, 24, 0.80)", popoverBg: "rgba(24, 18, 28, 0.97)", optionHover: "rgba(240, 126, 187, 0.22)", btnBg: "rgba(240, 126, 187, 0.16)", btnHoverBg: "rgba(240, 126, 187, 0.28)", btnHoverBorder: "rgba(240, 126, 187, 0.55)", pillBg: "rgba(33, 26, 34, 0.66)", pillSelected: "linear-gradient(135deg, rgba(240, 126, 187, 0.30), rgba(95, 214, 198, 0.20))", pillSelectedBorder: "rgba(240, 126, 187, 0.60)", scrollThumb: "rgba(240, 126, 187, 0.50)", scrollThumb2: "rgba(240, 126, 187, 0.42)", scrollThumbHover: "rgba(240, 126, 187, 0.66)" } }, en = {
  fonts: Sf,
  type: jf,
  radii: Nf,
  motion: Ef,
  spanRamp: Cf,
  palette: zf
};
function Ya(u) {
  const a = en.palette[u], c = en.spanRamp[u];
  return {
    "--canvas": a.canvas,
    "--surface": a.surface,
    "--surface-solid": a.card,
    "--ink": a.ink,
    "--muted": a.muted,
    "--faint": a.faint,
    "--line": a.line,
    "--line-strong": a.lineStrong,
    "--brand": a.brand,
    "--brand-bright": a.brandBright,
    "--brand-wash": a.brandWash,
    "--safe": a.safe,
    "--safe-wash": a.safeWash,
    "--warning": a.warning,
    "--warning-wash": a.warningWash,
    "--risk-ink": a.riskInk,
    "--risk-wash": a.riskWash,
    "--focus": a.focus,
    "--shadow": a.shadowRaised,
    "--shadow-whisper": a.shadowCard,
    "--span-wash-low": c.washLow,
    "--span-wash-high": c.washHigh,
    "--span-line-low": c.lineLow,
    "--span-line-high": c.lineHigh,
    "--span-safe": c.safe
  };
}
function Rf() {
  const u = {};
  for (const [a, c] of Object.entries(en.type))
    u[`--text-${a}-size`] = c.size, u[`--text-${a}-weight`] = String(c.weight), u[`--text-${a}-line`] = c.lineHeight, u[`--text-${a}-tracking`] = c.tracking;
  return u;
}
function Pf() {
  return {
    "--font-sans": en.fonts.sans,
    "--font-mono": en.fonts.mono,
    "--radius-card": en.radii.card,
    "--radius-input": en.radii.input,
    "--radius-panel": en.radii.panel,
    "--radius-pill": en.radii.pill,
    "--dur-fast": en.motion.duration.fast,
    "--dur-mid": en.motion.duration.mid,
    "--dur-slow": en.motion.duration.slow,
    "--ease-standard": en.motion.easing.standard,
    "--ease-entrance": en.motion.easing.entrance,
    ...Rf()
  };
}
function ba(u, a) {
  const c = Object.entries(a).map(([y, w]) => `  ${y}: ${w};`).join(`
`);
  return `${u} {
${c}
}`;
}
const Tf = [
  ba(".sirin-component-root", { ...Pf(), ...Ya("light") }),
  ba(".sirin-workspace[data-theme='dark']", Ya("dark"))
].join(`

`), ic = "recordedResultVerified", Lf = {
  recordedResultVerified: "Recorded result · verified — detection not live"
};
let _a = !1;
function Of(u) {
  if (u.querySelector(":scope > style[data-sirin-tokens]")) return;
  const a = document.createElement("style");
  a.setAttribute("data-sirin-tokens", ""), a.textContent = Tf, u.prepend(a);
}
function Ff() {
  if (_a || typeof FontFace > "u") return;
  _a = !0;
  const u = [
    new FontFace("Noto Color Emoji", `url(${kf})`, { style: "normal", weight: "400", unicodeRange: "U+1F9EA" }),
    new FontFace("Noto Color Emoji", `url(${wf})`, { style: "normal", weight: "400", unicodeRange: "U+1F984" })
  ];
  for (const a of u)
    document.fonts.add(a), a.load().catch(() => document.fonts.delete(a));
}
const $a = {
  analyze: {
    task: "faithfulness",
    mode: "generate",
    exampleId: null,
    context: "",
    question: "",
    answer: "",
    prompt: "",
    sourceRunId: null
  }
}, Mf = { theme: "light", motion: "subtle" }, oc = 240, sc = 180, If = 400, ec = /* @__PURE__ */ new Set(), Wf = /* @__PURE__ */ new Set(["consent_required", "busy", "empty_answer", "generation_unavailable", "judge_no_aligned_annotation"]), Ul = /* @__PURE__ */ new Map();
function Df(u) {
  return u ? { analyze: { ...$a.analyze, ...u.analyze, prompt: u.analyze.prompt ?? "", sourceRunId: u.analyze.sourceRunId ?? null }, quickPrompt: u.quickPrompt ?? "" } : { analyze: { ...$a.analyze }, quickPrompt: "" };
}
function nc() {
  var c, y, w, x;
  const u = (c = globalThis.sessionStorage) == null ? void 0 : c.getItem("sirin.client.id");
  if (u) return u;
  const a = ((w = (y = globalThis.crypto) == null ? void 0 : y.randomUUID) == null ? void 0 : w.call(y)) ?? `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return (x = globalThis.sessionStorage) == null || x.setItem("sirin.client.id", a), a;
}
function tc() {
  var u, a;
  return ((a = (u = globalThis.crypto) == null ? void 0 : u.randomUUID) == null ? void 0 : a.call(u)) ?? `action-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function De(u, a = !0) {
  return typeof u == "boolean" ? u : u && typeof u == "object" ? u.enabled : a;
}
function rc(u) {
  return u && typeof u == "object" ? u.reason ?? void 0 : void 0;
}
function kn(u) {
  return u ? u.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (a) => a.toUpperCase()) : "Unavailable";
}
function Ke(u) {
  return typeof u == "number" && Number.isFinite(u) ? u : null;
}
function uc(u) {
  return Math.min(1, Math.max(0, u));
}
function ac(u) {
  return u >= 0.995 ? "1.0" : u.toFixed(2).replace(/^0+/, "");
}
function Bo(u, a, c) {
  return `color-mix(in srgb, var(${a}) ${Math.round(uc(c) * 100)}%, var(${u}))`;
}
function Al(u, a, c) {
  return a === !0 || u !== null && c !== null && u >= c;
}
function cc(u, a) {
  const c = a ?? 0;
  return uc((u - c) / Math.max(1 - c, 1e-6));
}
function Cr(u, a) {
  const c = Ke(u);
  return c === null ? "No score" : ["calibrated_probability", "calibratedProbability", "categorical_probabilities", "categoricalProbabilities"].includes(a ?? "") ? `${Math.round(c * 100)}%` : c.toFixed(c < 10 ? 2 : 1);
}
function dc(u, a) {
  const c = a == null ? void 0 : a.trim();
  return c || (["calibrated_probability", "calibratedProbability"].includes(u ?? "") ? "calibrated probability" : ["relative_within_answer", "relativeWithinAnswer"].includes(u ?? "") ? "relative within this answer — not comparable across runs" : ["thresholded_raw_score", "thresholdedRawScore"].includes(u ?? "") ? "raw score vs decision threshold τ" : ["categorical_probabilities", "categoricalProbabilities"].includes(u ?? "") ? "class confidence" : ["span_agreement", "spanAgreement"].includes(u ?? "") ? "judge agreement" : u === "verdict" ? "verdict" : null);
}
function Bl(u) {
  if (typeof u != "string") return "neutral";
  const a = u.trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ");
  return ["risk", "suspect", "unsupported", "hallucinated", "hallucination", "failed", "error", "unanswerable", "unsafe"].includes(a) ? "risk" : ["safe", "supported", "faithful", "answerable", "passed", "grounded", "healthy"].includes(a) ? "safe" : "neutral";
}
function ql(u, a, c) {
  const y = (u == null ? void 0 : u[a]) ?? (u == null ? void 0 : u[c]);
  return y == null || y === "" ? "Not configured" : String(y);
}
function fc({ status: u }) {
  return /* @__PURE__ */ o.jsx("span", { className: `status-dot ${Bl(u)}`, "aria-hidden": "true" });
}
function sn({ name: u }) {
  const a = {
    analyze: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M4 17.5 9 12l3 3 7-8" }),
      /* @__PURE__ */ o.jsx("path", { d: "M15 7h4v4" })
    ] }),
    runs: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M6 5h12M6 12h12M6 19h12" }),
      /* @__PURE__ */ o.jsx("path", { d: "M3 5h.01M3 12h.01M3 19h.01" })
    ] }),
    diagnostics: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "M4 14h3l2-7 4 11 2-7h5" }) }),
    arrow: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
    spark: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z" }),
      /* @__PURE__ */ o.jsx("path", { d: "m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7Z" })
    ] }),
    download: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 3v12m-5-5 5 5 5-5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 21h14" })
    ] }),
    upload: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 21V9m-5 5 5-5 5 5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 3h14" })
    ] })
  };
  return /* @__PURE__ */ o.jsx("svg", { className: "icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: a[u] });
}
function Vf({
  workspace: u,
  onWorkspace: a,
  setup: c,
  title: y,
  subtitle: w
}) {
  const [x, T] = fe.useState(!1), L = fe.useId();
  return fe.useEffect(() => {
    if (!x) return;
    const z = (k) => {
      k.key === "Escape" && T(!1);
    };
    return globalThis.addEventListener("keydown", z), () => globalThis.removeEventListener("keydown", z);
  }, [x]), /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsxs("header", { className: "shell-header", children: [
      /* @__PURE__ */ o.jsxs("button", { className: "brand", type: "button", onClick: () => a("analyze"), "aria-label": "SIRIN Analyze home", children: [
        /* @__PURE__ */ o.jsx("img", { src: xf, alt: "" }),
        /* @__PURE__ */ o.jsxs("span", { children: [
          /* @__PURE__ */ o.jsx("b", { children: "SIRIN" }),
          /* @__PURE__ */ o.jsx("small", { children: "Honesty, made visible." })
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("nav", { className: "workspace-tabs", "aria-label": "Workspace", children: ["analyze", "runs", "diagnostics"].map((z) => /* @__PURE__ */ o.jsxs("button", { type: "button", "data-workspace-tab": z, className: u === z ? "active" : "", "aria-current": u === z ? "page" : void 0, onClick: () => a(z), children: [
        /* @__PURE__ */ o.jsx(sn, { name: z }),
        kn(z)
      ] }, z)) }),
      /* @__PURE__ */ o.jsxs("button", { className: "setup-chip", type: "button", onClick: () => T((z) => !z), "aria-expanded": x, "aria-controls": L, children: [
        /* @__PURE__ */ o.jsxs("span", { className: "setup-summary", children: [
          /* @__PURE__ */ o.jsx("small", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("b", { children: ql(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsx(sn, { name: "arrow" })
      ] })
    ] }),
    x && /* @__PURE__ */ o.jsxs("div", { className: "setup-popover", id: L, role: "region", "aria-label": "Active setup", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Active setup" }),
      /* @__PURE__ */ o.jsxs("dl", { children: [
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("dd", { children: ql(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Generator" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.providerLabel) ?? (c == null ? void 0 : c.modelId) ?? ql(c, "modelLabel", "model") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Device" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.device) ?? "Automatic" })
        ] }),
        (c == null ? void 0 : c.layer) !== void 0 && c.layer !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Layer" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.layer })
        ] }),
        (c == null ? void 0 : c.threshold) !== void 0 && c.threshold !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Threshold" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.threshold })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("section", { className: "page-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u === "analyze" ? "Evidence workspace" : kn(u) }),
      /* @__PURE__ */ o.jsx("h1", { children: y ?? (u === "analyze" ? "See where an answer leaves the evidence." : u === "runs" ? "Every result, with its receipts." : u === "compare" ? "Two detectors, one answer, side by side." : "Know what SIRIN is running.") }),
      /* @__PURE__ */ o.jsx("p", { children: w ?? (u === "analyze" ? "Generate or supply an answer. SIRIN checks it against context and makes uncertainty legible." : u === "runs" ? "Review immutable outcomes and carry portable records between sessions." : u === "compare" ? "Both detectors score the same answer. Localization overlap is comparable; scores are only compared when their scales are." : "Inspect the active runtime without exposing sensitive internals.") })
    ] })
  ] });
}
function et({ label: u, hint: a, children: c }) {
  return /* @__PURE__ */ o.jsxs("label", { className: "field", children: [
    /* @__PURE__ */ o.jsxs("span", { children: [
      u,
      a && /* @__PURE__ */ o.jsx("small", { children: a })
    ] }),
    c
  ] });
}
function Hl({ value: u, onChange: a, ariaLabel: c, children: y }) {
  return /* @__PURE__ */ o.jsxs("span", { className: "select-wrap", children: [
    /* @__PURE__ */ o.jsx("select", { value: u, "aria-label": c, onChange: a, children: y }),
    /* @__PURE__ */ o.jsx("svg", { className: "select-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m6 9 6 6 6-6" }) })
  ] });
}
function Uf({ examples: u, selected: a, onSelect: c }) {
  return u.length ? /* @__PURE__ */ o.jsxs("div", { className: "examples", children: [
    /* @__PURE__ */ o.jsx("span", { children: "Try an example" }),
    /* @__PURE__ */ o.jsx("div", { className: "example-list", children: u.map((y) => /* @__PURE__ */ o.jsx("button", { type: "button", disabled: !!y.disabledReason, title: y.disabledReason ?? y.description, className: a === y.id ? "selected" : "", onClick: () => c(y), children: y.label }, y.id)) })
  ] }) : null;
}
function qf(u, a) {
  const c = u == null ? void 0 : u.status, y = u != null && u.runId ? a.find((x) => x.id === u.runId) : void 0, w = `${(y == null ? void 0 : y.origin) ?? ""} ${(y == null ? void 0 : y.mode) ?? ""} ${(y == null ? void 0 : y.task) ?? ""}`;
  return c === "running" ? /answerability/i.test(w) ? { label: "Checking answerability…", detail: "Judging whether the question is answerable from the context." } : /generat|quickPrompt/i.test(w) ? { label: "Generating…", detail: "The model is drafting an answer, then SIRIN scores it against the context." } : { label: "Scoring…", detail: "Running the detector over the answer." } : c === "queued" ? { label: "Queued…", detail: "Waiting for the runtime to pick up this run." } : { label: "Working…", detail: "The result will appear here when the operation finishes." };
}
function Zo({ activity: u, runs: a = [] }) {
  const { label: c, detail: y } = qf(u, a);
  return /* @__PURE__ */ o.jsxs("section", { className: "result-card activity-card", "aria-live": "polite", "aria-busy": "true", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "activity-status", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Working" }),
      /* @__PURE__ */ o.jsx("h2", { children: c }),
      /* @__PURE__ */ o.jsx("p", { children: y })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "skeleton-lines", "aria-hidden": "true", children: [
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {})
    ] })
  ] });
}
function Hf({ answer: u, onComplete: a }) {
  const c = fe.useRef(a);
  c.current = a;
  const [y, w] = fe.useState("");
  return fe.useEffect(() => {
    w("");
    const x = u.match(/\S+\s*/g) ?? [u];
    let T = 0;
    const L = globalThis.setInterval(() => {
      T += 1, w(x.slice(0, T).join("")), T >= x.length && (globalThis.clearInterval(L), c.current());
    }, Math.max(24, Math.min(70, 900 / Math.max(x.length, 1))));
    return () => globalThis.clearInterval(L);
  }, [u]), /* @__PURE__ */ o.jsxs("p", { className: "answer-copy", children: [
    y,
    /* @__PURE__ */ o.jsx("span", { className: y.length < u.length ? "caret" : "caret hidden", "aria-hidden": "true" })
  ] });
}
function Af({ answer: u, result: a }) {
  var T;
  if (!((T = a.segments) != null && T.length)) return /* @__PURE__ */ o.jsx("p", { className: "answer-copy", children: u || "No answer was returned." });
  const c = Ke(a.threshold), y = a.segments.map((L) => {
    const z = Ke(L.score);
    return Al(z, L.verdict, c) ? z ?? 1 : -1;
  }), w = y.indexOf(Math.max(...y));
  let x = 0;
  return /* @__PURE__ */ o.jsx("p", { className: "answer-copy segmented", children: a.segments.map((L, z) => {
    const k = Ke(L.score), H = Al(k, L.verdict, c), B = L.startCodePoint !== void 0 ? `characters ${L.startCodePoint}–${L.endCodePoint}` : "text segment", J = [B, k !== null ? `score ${k.toFixed(2)}` : null, c !== null ? `τ ${c.toFixed(3)}` : null, "probe confidence, not calibrated"].filter(Boolean).join(" · ");
    if (H) {
      const le = k !== null ? cc(k, c) : 1, ve = Bo("--span-line-low", "--span-line-high", le), K = { "--seg-wash": Bo("--span-wash-low", "--span-wash-high", le), "--seg-line": ve, borderBottomWidth: le >= 0.5 ? "3px" : "2px", "--d": `${oc + x * sc}ms` }, X = z === w ? "evidence graded is-peak" : "evidence graded";
      return x += 1, /* @__PURE__ */ o.jsxs("span", { className: X, style: K, tabIndex: 0, "aria-label": `${L.text}, ${J}`, title: J, children: [
        L.text,
        k !== null && /* @__PURE__ */ o.jsx("sup", { className: "evidence-badge", children: ac(k) })
      ] }, `${B}-${z}`);
    }
    return k !== null ? /* @__PURE__ */ o.jsx("span", { className: "evidence below", title: J, children: L.text }, `${B}-${z}`) : /* @__PURE__ */ o.jsx("span", { className: "evidence", children: L.text }, `${B}-${z}`);
  }) });
}
function Bf({ result: u }) {
  const a = Ke(u.threshold), c = (u.segments ?? []).filter((L) => Al(Ke(L.score), L.verdict, a)), y = c.map((L) => Ke(L.score)).filter((L) => L !== null), w = y.length ? Math.max(...y) : null, x = c.length ? Bo("--span-line-low", "--span-line-high", w !== null ? cc(w, a) : 1) : "var(--span-safe)", T = c.length ? `${c.length} suspect ${c.length === 1 ? "span" : "spans"}${w !== null ? ` · max risk ${w.toFixed(2)}` : ""}` : "No spans above threshold";
  return /* @__PURE__ */ o.jsxs("div", { className: "span-footer", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "span-verdict", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-verdict-dot", style: { background: x }, "aria-hidden": "true" }),
      T
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "span-legend", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-word", children: "risk" }),
      a !== null && /* @__PURE__ */ o.jsxs("span", { className: "span-legend-num", children: [
        "τ ",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-bar", "aria-hidden": "true" }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-num", children: "1.00" })
    ] })
  ] });
}
function Xf({ result: u }) {
  var w, x, T, L, z;
  const a = (w = u.spans) != null && w.length ? u.spans : (u.segments ?? []).filter((k) => k.verdict === !0).map((k) => ({ text: k.text, startCodePoint: k.startCodePoint, endCodePoint: k.endCodePoint, score: k.score, scoreKind: u.scoreSemantics, verdict: "suspect" })), c = u.categories ?? (Array.isArray(u.classes) ? u.classes : Object.entries(u.classes ?? {}).map(([k, H]) => ({ label: k, score: H })));
  return !(a.length || (x = u.claims) != null && x.length || c.length || u.rationale || (T = u.values) != null && T.length) ? null : /* @__PURE__ */ o.jsxs("details", { className: "evidence-details", children: [
    /* @__PURE__ */ o.jsx("summary", { children: "Evidence details" }),
    a.length ? /* @__PURE__ */ o.jsx("div", { className: "evidence-list", "aria-label": "Suspect spans", children: a.map((k, H) => /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text }),
        /* @__PURE__ */ o.jsx("small", { children: k.startCodePoint !== void 0 ? `Characters ${k.startCodePoint}–${k.endCodePoint}` : "Span evidence" })
      ] }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        Ke(k.score) !== null ? ac(Ke(k.score)) : Cr(k.score, k.scoreKind),
        " · ",
        k.verdict ?? "scored"
      ] })
    ] }, `${k.startCodePoint}-${H}`)) }) : null,
    (L = u.claims) != null && L.length ? /* @__PURE__ */ o.jsx("div", { className: "claim-list", children: u.claims.map((k, H) => /* @__PURE__ */ o.jsxs("article", { className: Bl(k.verdict), children: [
      /* @__PURE__ */ o.jsx(fc, { status: k.supported === !0 ? "safe" : k.supported === !1 ? "risk" : k.verdict }),
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text ?? k.claim ?? `Claim ${H + 1}` }),
        k.rationale && /* @__PURE__ */ o.jsx("p", { children: k.rationale })
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: k.verdict ?? Cr(k.score) })
    ] }, H)) }) : null,
    c.length ? /* @__PURE__ */ o.jsx("div", { className: "class-list", "aria-label": "Class scores", children: c.map((k) => /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("span", { children: kn(k.label) }),
      /* @__PURE__ */ o.jsx("i", { children: /* @__PURE__ */ o.jsx("b", { style: { width: `${Math.max(0, Math.min(100, k.score * 100))}%` } }) }),
      /* @__PURE__ */ o.jsx("strong", { children: Cr(k.score, "categorical_probabilities") })
    ] }, k.label)) }) : null,
    (z = u.values) != null && z.length ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("div", { className: "mini-bars", "aria-hidden": "true", children: u.values.map((k, H) => /* @__PURE__ */ o.jsx("i", { style: { height: `${10 + Math.max(0, Math.min(1, k)) * 54}px` } }, H)) }),
      /* @__PURE__ */ o.jsx("ol", { className: "sr-only", "aria-label": "Relative token scores", children: u.values.map((k, H) => /* @__PURE__ */ o.jsxs("li", { children: [
        "Item ",
        H + 1,
        ": ",
        k.toFixed(3)
      ] }, H)) })
    ] }) : null,
    (u.rationale || u.note) && /* @__PURE__ */ o.jsx("p", { className: "rationale", children: u.rationale ?? u.note })
  ] });
}
function Zf({ run: u }) {
  const a = u.provenance ?? {}, c = u.origin === ic, y = c && typeof a.integritySha256 == "string" ? a.integritySha256 : null, w = Object.entries(a).filter(([x, T]) => x !== (y ? "integritySha256" : "") && (typeof T == "string" || typeof T == "number" || typeof T == "boolean"));
  return /* @__PURE__ */ o.jsxs("div", { className: "provenance", children: [
    /* @__PURE__ */ o.jsx("span", { children: c ? "Recorded result · verified" : kn(u.origin ?? u.mode ?? "live run") }),
    (u.setupSnapshot ?? u.setup) && /* @__PURE__ */ o.jsx("span", { children: ql(u.setupSnapshot ?? u.setup, "detectorPreset", "detectorLabel") }),
    u.staleSetup && /* @__PURE__ */ o.jsx("span", { className: "warning", children: "Different setup" }),
    u.sourceRunId && /* @__PURE__ */ o.jsxs("span", { children: [
      "Source ",
      u.sourceRunId
    ] }),
    y && /* @__PURE__ */ o.jsxs("span", { title: y, children: [
      "Checkpoint ",
      y.slice(0, 12),
      "…"
    ] }),
    w.slice(0, 3).map(([x, T]) => /* @__PURE__ */ o.jsxs("span", { children: [
      kn(x),
      ": ",
      String(T)
    ] }, x))
  ] });
}
function Jf({ timings: u }) {
  if (!u) return null;
  const c = [["generation", u.generationSeconds], ["detection", u.detectionSeconds], ["total", u.totalSeconds]].map(([y, w]) => [y, Ke(w)]).filter(([, y]) => y !== null);
  return c.length ? /* @__PURE__ */ o.jsx("div", { className: "latency-strip", "aria-label": "Run latency", children: c.map(([y, w], x) => /* @__PURE__ */ o.jsxs("span", { children: [
    x > 0 ? "· " : "",
    y,
    " ",
    /* @__PURE__ */ o.jsxs("b", { children: [
      w.toFixed(1),
      "s"
    ] })
  ] }, y)) }) : null;
}
function Jo({ run: u, motion: a, onAction: c, onPrepareRerun: y }) {
  var Xe, Fe, Ve, V;
  const w = u.analysis ?? u.result ?? {}, x = w.scoreSemantics ?? u.scoreSemantics, T = w.score ?? w.confidence ?? u.score, L = dc(x, w.scaleLabel ?? u.scaleLabel), z = (w.segments ?? []).some((b) => Ke(b.score) !== null || b.verdict === !0), k = w.verdict ?? u.verdict, H = w.label ?? (typeof k == "string" ? k : null) ?? (u.status === "failed" ? "Failed" : "Result"), B = u.origin === ic, J = !B && /replay|recorded/i.test(`${u.origin ?? ""} ${u.mode ?? ""}`), le = ((Xe = globalThis.matchMedia) == null ? void 0 : Xe.call(globalThis, "(prefers-reduced-motion: reduce)").matches) ?? !1, [ve] = fe.useState(() => {
    const b = !ec.has(u.id);
    return ec.add(u.id), b;
  }), K = a !== "static" && !le && ve, X = J && K, [ie, Ee] = fe.useState(!X), pe = Ke(w.threshold), ge = (w.segments ?? []).filter((b) => Al(Ke(b.score), b.verdict, pe)).length, Pe = z && K, we = oc + ge * sc + If, G = typeof u.error == "string" ? u.error : (Fe = u.error) == null ? void 0 : Fe.message, oe = u.error && typeof u.error == "object" ? u.error : null;
  return /* @__PURE__ */ o.jsxs("section", { className: `result-card ${Bl(k ?? H)}${Pe ? " is-reveal" : ""}`, style: Pe ? { "--reveal-total": `${we}ms` } : void 0, "aria-live": "polite", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "result-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Outcome" }),
        /* @__PURE__ */ o.jsx("h2", { children: H }),
        /* @__PURE__ */ o.jsx("p", { children: w.summary ?? (u.status === "partial" ? "The answer was preserved, but part of analysis did not complete." : "Evidence is shown in the answer and details below.") })
      ] }),
      !z && Ke(T) !== null && L && /* @__PURE__ */ o.jsxs("div", { className: "score-orb", children: [
        /* @__PURE__ */ o.jsx("strong", { children: Cr(T, x) }),
        /* @__PURE__ */ o.jsx("span", { children: L }),
        ["thresholded_raw_score", "thresholdedRawScore"].includes(x ?? "") && pe !== null && /* @__PURE__ */ o.jsxs("small", { className: "decision-band", children: [
          "vs τ ",
          pe.toFixed(2)
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "answer-block", children: [
      /* @__PURE__ */ o.jsxs("div", { className: "answer-label", children: [
        /* @__PURE__ */ o.jsx("span", { children: "Answer" }),
        /* @__PURE__ */ o.jsx("small", { children: B ? Lf.recordedResultVerified : J ? "Recorded answer · live detection" : u.origin === "importedSnapshot" || u.origin === "imported" ? "Imported snapshot" : /answerability/i.test(u.origin ?? u.mode ?? "") ? "Answerability · live detection" : /supplied/i.test(u.origin ?? u.mode ?? "") ? "Supplied answer · live detection" : "Generated now" })
      ] }),
      X && !ie ? /* @__PURE__ */ o.jsx(Hf, { answer: u.answer ?? "", onComplete: () => Ee(!0) }) : /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
        /* @__PURE__ */ o.jsx(Af, { answer: u.answer ?? "", result: w }),
        z && /* @__PURE__ */ o.jsx(Bf, { result: w })
      ] })
    ] }),
    w.unavailableReason && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice warning", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Analysis unavailable" }),
      /* @__PURE__ */ o.jsx("span", { children: w.unavailableReason })
    ] }),
    G && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error", children: [
      /* @__PURE__ */ o.jsx("b", { children: u.status === "partial" ? "Detection did not finish" : "Run failed" }),
      /* @__PURE__ */ o.jsx("span", { children: G }),
      (oe == null ? void 0 : oe.correlationId) && !Wf.has(oe.code ?? "") && /* @__PURE__ */ o.jsxs("small", { children: [
        "Reference ",
        oe.correlationId
      ] })
    ] }),
    (Ve = u.warnings) == null ? void 0 : Ve.map((b, Ce) => /* @__PURE__ */ o.jsx("div", { className: "inline-notice warning", children: b }, Ce)),
    /* @__PURE__ */ o.jsx(Xf, { result: w }),
    /* @__PURE__ */ o.jsx(Zf, { run: u }),
    /* @__PURE__ */ o.jsx(Jf, { timings: u.timings }),
    /* @__PURE__ */ o.jsxs("div", { className: "result-actions", children: [
      B && ((V = u.inputs) == null ? void 0 : V.exampleId) && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", title: "Replays the verified answer and runs the probe live. Loads the model.", onClick: () => {
        var b, Ce, Ue;
        return c("submit", { task: "faithfulness", mode: "recordedReplay", context: ((b = u.inputs) == null ? void 0 : b.context) ?? "", question: ((Ce = u.inputs) == null ? void 0 : Ce.question) ?? "", suppliedAnswer: u.answer ?? "", prompt: "", exampleId: (Ue = u.inputs) == null ? void 0 : Ue.exampleId });
      }, children: [
        /* @__PURE__ */ o.jsx(sn, { name: "spark" }),
        "Run it live"
      ] }),
      (u.status === "partial" || u.status === "failed") && u.answer && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => c("retryDetection", { runId: u.id }), children: "Retry detection" }),
      (u.origin === "importedSnapshot" || u.origin === "imported" || u.immutable) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => y(u), children: "Rerun with current setup" }),
      /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", onClick: () => c("exportRun", { runId: u.id }), children: [
        /* @__PURE__ */ o.jsx(sn, { name: "download" }),
        "Export run"
      ] })
    ] })
  ] });
}
function Kf({ payload: u, draft: a, setDraft: c, busy: y, motion: w, onAction: x, onPrepareRerun: T, onCompare: L }) {
  var Ve;
  const z = u.capabilities ?? {}, k = z, H = String(((Ve = u.setup) == null ? void 0 : Ve.task) ?? "faithfulness"), B = H === a.task ? !0 : { enabled: !1, reason: `The active detector supports ${kn(H)}, not ${kn(a.task)}.` }, J = a.task === "answerability" ? k.canAnswerability ?? B : B, le = a.task === "faithfulness" && a.mode === "generate" ? z.canGenerate : !0, ve = a.prompt.trim().length > 0 || a.context.trim().length > 0 && a.question.trim().length > 0, K = De(J) && De(le) && ve && (a.task === "answerability" || a.mode === "generate" || a.answer.trim().length > 0), X = u.availablePresets ?? [], [ie, Ee] = fe.useState(!1), [pe, ge] = fe.useState(""), Pe = () => {
    const V = pe || X[0];
    !V || !K || y || L(V, {
      task: a.task,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId
    });
  }, we = u.examples ?? [], G = we.find((V) => V.id === a.exampleId), oe = !!(G && (G.recordedAnswer || G.answer)), Xe = (V) => c({
    task: V.task ?? a.task,
    mode: a.mode,
    exampleId: V.id,
    context: V.context ?? "",
    question: V.question ?? "",
    answer: V.answer ?? V.recordedAnswer ?? "",
    prompt: V.prompt ?? "",
    sourceRunId: null
  }, !0), Fe = (V) => {
    if (V.preventDefault(), !K || y) return;
    const b = a.task === "answerability" ? "answerability" : a.sourceRunId && a.prompt && !a.context && !a.question ? "quickPrompt" : a.mode === "generate" ? "generateAndScore" : "scoreSuppliedAnswer";
    x("submit", {
      task: a.task,
      mode: b,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId,
      ...a.sourceRunId ? { sourceRunId: a.sourceRunId } : {}
    }), a.sourceRunId && c({ ...a, sourceRunId: null });
  };
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content analyze-workspace", children: [
    /* @__PURE__ */ o.jsx(Uf, { examples: we.filter((V) => !V.task || V.task === a.task), selected: a.exampleId, onSelect: Xe }),
    /* @__PURE__ */ o.jsxs("form", { className: "analysis-form", onSubmit: Fe, children: [
      /* @__PURE__ */ o.jsxs("div", { className: "form-row", children: [
        /* @__PURE__ */ o.jsx(et, { label: "Task", children: /* @__PURE__ */ o.jsxs(Hl, { value: a.task, onChange: (V) => {
          const b = V.target.value;
          c({ ...a, task: b, mode: b === "answerability" ? "generate" : a.mode }, !0);
        }, children: [
          /* @__PURE__ */ o.jsx("option", { value: "faithfulness", disabled: H !== "faithfulness", children: "Faithfulness" }),
          /* @__PURE__ */ o.jsx("option", { value: "answerability", disabled: !De(k.canAnswerability ?? H === "answerability"), children: "Answerability" })
        ] }) }),
        a.task === "faithfulness" && /* @__PURE__ */ o.jsx(et, { label: "Answer source", children: /* @__PURE__ */ o.jsxs(Hl, { value: a.mode, onChange: (V) => c({ ...a, mode: V.target.value }, !0), children: [
          /* @__PURE__ */ o.jsx("option", { value: "generate", disabled: !De(z.canGenerate), children: "Generate an answer" }),
          /* @__PURE__ */ o.jsx("option", { value: "supplied", children: "Score supplied answer" })
        ] }) })
      ] }),
      a.prompt && /* @__PURE__ */ o.jsxs("details", { className: "prompt-disclosure", children: [
        /* @__PURE__ */ o.jsxs("summary", { children: [
          /* @__PURE__ */ o.jsx("svg", { className: "disclosure-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
          /* @__PURE__ */ o.jsx("span", { children: "Exact model prompt" }),
          /* @__PURE__ */ o.jsxs("span", { className: "disclosure-count", children: [
            a.prompt.length.toLocaleString(),
            " characters"
          ] })
        ] }),
        /* @__PURE__ */ o.jsx(et, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 5, value: a.prompt, placeholder: "Verified example or imported prompt…", onChange: (V) => c({ ...a, prompt: V.target.value, exampleId: null }), onBlur: () => c(a, !0) }) })
      ] }),
      /* @__PURE__ */ o.jsx(et, { label: "Context", hint: `${a.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ o.jsx("textarea", { rows: 7, value: a.context, placeholder: "Paste the source material the answer must stay grounded in…", onChange: (V) => c({ ...a, context: V.target.value }), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsx(et, { label: "Question", children: /* @__PURE__ */ o.jsx("textarea", { rows: 2, value: a.question, placeholder: "What should the model answer from this context?", onChange: (V) => c({ ...a, question: V.target.value }), onBlur: () => c(a, !0) }) }),
      a.task === "faithfulness" && a.mode === "supplied" && /* @__PURE__ */ o.jsx(et, { label: "Answer to score", children: /* @__PURE__ */ o.jsx("textarea", { rows: 4, value: a.answer, placeholder: "Paste the answer that should be checked…", onChange: (V) => c({ ...a, answer: V.target.value }), onBlur: () => c(a, !0) }) }),
      !De(J) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: rc(J) ?? "The active detector does not support this task." }),
      !De(le) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: rc(le) ?? "Generation is not available with the active setup." }),
      a.sourceRunId && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice info", children: [
        /* @__PURE__ */ o.jsx("b", { children: "Imported run prepared" }),
        /* @__PURE__ */ o.jsx("span", { children: "Review these inputs, then submit explicitly with the current setup." })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        oe && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: y, onClick: () => x("submit", { task: (G == null ? void 0 : G.task) ?? "faithfulness", mode: "recordedReplay", context: a.context, question: a.question, suppliedAnswer: (G == null ? void 0 : G.recordedAnswer) ?? (G == null ? void 0 : G.answer) ?? "", prompt: "", exampleId: G == null ? void 0 : G.id }), children: [
          /* @__PURE__ */ o.jsx(sn, { name: "spark" }),
          "Replay recorded answer"
        ] }),
        /* @__PURE__ */ o.jsxs("button", { className: oe ? "secondary" : "primary", type: "submit", disabled: !K || y, children: [
          /* @__PURE__ */ o.jsx(sn, { name: "spark" }),
          a.task === "answerability" ? "Check answerability" : a.mode === "supplied" ? "Score answer" : "Generate & score"
        ] }),
        X.length > 0 && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: y, "aria-expanded": ie, onClick: () => Ee((V) => !V), children: "Compare detectors…" })
      ] }),
      ie && X.length > 0 && /* @__PURE__ */ o.jsxs("div", { className: "compare-picker", children: [
        /* @__PURE__ */ o.jsx(et, { label: "Second detector (B)", hint: "scores the same answer", children: /* @__PURE__ */ o.jsx(Hl, { ariaLabel: "Second detector for comparison", value: pe || X[0], onChange: (V) => ge(V.target.value), children: X.map((V) => /* @__PURE__ */ o.jsx("option", { value: V, children: V }, V)) }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: !K || y, onClick: Pe, children: [
          /* @__PURE__ */ o.jsx(sn, { name: "spark" }),
          "Run comparison"
        ] }),
        !K && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: "Enter a context and question (or an answer to score) first." })
      ] })
    ] }),
    y ? /* @__PURE__ */ o.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ o.jsx(Jo, { run: u.selectedRun, motion: w, onAction: x, onPrepareRerun: T }, u.selectedRun.id) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(sn, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "Your evidence map will appear here." }),
      /* @__PURE__ */ o.jsx("p", { children: "Results lead with the outcome, then reveal only the detail each detector can honestly support." })
    ] })
  ] });
}
function Qf({ agreement: u }) {
  const a = [
    { key: "both", label: "Both flag", count: u.both, color: "var(--span-line-high)" },
    { key: "aOnly", label: "A only", count: u.aOnly, color: "var(--span-line-low)" },
    { key: "bOnly", label: "B only", count: u.bOnly, color: "var(--brand)" },
    { key: "neither", label: "Neither", count: u.neither, color: "var(--safe)" }
  ], c = a.reduce((x, T) => x + T.count, 0), y = c || 1, w = (x) => Math.round(x / y * 100);
  return /* @__PURE__ */ o.jsxs("div", { className: "agreement", children: [
    /* @__PURE__ */ o.jsxs("p", { className: "eyebrow", children: [
      "Localization agreement · ",
      c,
      " characters"
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-bar", role: "img", "aria-label": a.map((x) => `${x.label} ${x.count}`).join(", "), children: a.map((x) => x.count > 0 ? /* @__PURE__ */ o.jsx("span", { style: { width: `${x.count / y * 100}%`, background: x.color }, title: `${x.label}: ${x.count} (${w(x.count)}%)` }, x.key) : null) }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-legend", children: a.map((x) => /* @__PURE__ */ o.jsxs("span", { children: [
      /* @__PURE__ */ o.jsx("i", { style: { background: x.color }, "aria-hidden": "true" }),
      x.label,
      " ",
      /* @__PURE__ */ o.jsx("b", { children: x.count }),
      " ",
      /* @__PURE__ */ o.jsxs("em", { children: [
        w(x.count),
        "%"
      ] })
    ] }, x.key)) })
  ] });
}
function Gf({ compare: u }) {
  const a = Ke(u.deltaScore);
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-verdict", children: [
    u.agreement ? /* @__PURE__ */ o.jsx(Qf, { agreement: u.agreement }) : /* @__PURE__ */ o.jsxs("div", { className: "compare-note", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Localization agreement" }),
      /* @__PURE__ */ o.jsx("p", { children: u.agreementNote ?? "No per-character overlap is available for these detectors." })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "compare-delta", children: a !== null ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsxs("span", { className: "compare-delta-value", children: [
        a > 0 ? "+" : "",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: u.deltaNote })
    ] }) : /* @__PURE__ */ o.jsx("span", { className: "compare-note-line", children: u.deltaNote || "Different score scales — localization overlap only." }) })
  ] });
}
function lc({ label: u, preset: a, run: c, motion: y, onAction: w, onPrepareRerun: x }) {
  var k, H;
  const T = ((k = c == null ? void 0 : c.analysis) == null ? void 0 : k.scoreSemantics) ?? ((H = c == null ? void 0 : c.setupSnapshot) == null ? void 0 : H.scoreSemantics), L = dc(T), z = c ? ["queued", "running"].includes(c.status) : !1;
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-column", children: [
    /* @__PURE__ */ o.jsxs("header", { className: "compare-col-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u }),
      /* @__PURE__ */ o.jsx("h3", { children: a ?? "Detector" }),
      L && /* @__PURE__ */ o.jsx("small", { children: L })
    ] }),
    c ? z ? /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Scoring…" }),
      /* @__PURE__ */ o.jsx("p", { children: "Running this detector over the shared answer." })
    ] }) : /* @__PURE__ */ o.jsx(Jo, { run: c, motion: y, onAction: w, onPrepareRerun: x }, c.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Waiting…" }),
      /* @__PURE__ */ o.jsx("p", { children: "This side scores the same answer once it is available." })
    ] })
  ] });
}
function Yf({ payload: u, motion: a, onAction: c, onPrepareRerun: y, onBack: w }) {
  const x = u.compare;
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content compare-workspace", children: [
    /* @__PURE__ */ o.jsx("div", { className: "compare-head", children: /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", onClick: w, children: "← Back to Analyze" }) }),
    x ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx(Gf, { compare: x }),
      /* @__PURE__ */ o.jsxs("div", { className: "compare-grid", children: [
        /* @__PURE__ */ o.jsx(lc, { label: "Detector A", preset: x.presetA, run: x.runA, motion: a, onAction: c, onPrepareRerun: y }),
        /* @__PURE__ */ o.jsx(lc, { label: "Detector B", preset: x.presetB, run: x.runB, motion: a, onAction: c, onPrepareRerun: y })
      ] })
    ] }) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(sn, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "No comparison yet." }),
      /* @__PURE__ */ o.jsx("p", { children: "Open “Compare detectors…” in Analyze to score one answer with two detectors side by side." })
    ] })
  ] });
}
function bf(u) {
  if (!u) return "Time unavailable";
  const a = new Date(u);
  return Number.isNaN(a.valueOf()) ? u : new Intl.DateTimeFormat(void 0, { dateStyle: "medium", timeStyle: "short" }).format(a);
}
function _f({ runs: u, selectedId: a, onSelect: c, onAnalyze: y }) {
  const [w, x] = fe.useState(""), [T, L] = fe.useState("all"), z = u.filter((k) => (T === "all" || k.status === T) && `${k.title ?? ""} ${k.question ?? ""} ${k.prompt ?? ""} ${k.answer ?? ""}`.toLowerCase().includes(w.toLowerCase()));
  return /* @__PURE__ */ o.jsxs("section", { className: "run-browser", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "section-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "History" }),
        /* @__PURE__ */ o.jsxs("h2", { children: [
          u.length,
          " ",
          u.length === 1 ? "run" : "runs"
        ] })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "filters", children: [
        /* @__PURE__ */ o.jsx("input", { type: "search", "aria-label": "Search runs", value: w, placeholder: "Search runs", onChange: (k) => x(k.target.value) }),
        /* @__PURE__ */ o.jsxs(Hl, { ariaLabel: "Filter runs by status", value: T, onChange: (k) => L(k.target.value), children: [
          /* @__PURE__ */ o.jsx("option", { value: "all", children: "All outcomes" }),
          /* @__PURE__ */ o.jsx("option", { value: "succeeded", children: "Succeeded" }),
          /* @__PURE__ */ o.jsx("option", { value: "partial", children: "Partial" }),
          /* @__PURE__ */ o.jsx("option", { value: "failed", children: "Failed" }),
          /* @__PURE__ */ o.jsx("option", { value: "interrupted", children: "Interrupted" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "run-list", children: z.length ? z.map((k) => /* @__PURE__ */ o.jsxs("button", { type: "button", className: a === k.id ? "selected" : "", onClick: () => c(k), children: [
      /* @__PURE__ */ o.jsx(fc, { status: k.status }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.title ?? k.question ?? k.prompt ?? `Run ${k.id}` }),
        /* @__PURE__ */ o.jsxs("small", { children: [
          bf(k.completedAt ?? k.createdAt),
          " · ",
          kn(k.task),
          " · ",
          kn(k.status)
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("strong", { children: typeof k.verdict == "boolean" ? k.task === "answerability" ? k.verdict ? "Answerable" : "Unanswerable" : k.verdict ? "Unsupported" : "Supported" : k.verdict ?? Cr(k.score, k.scoreSemantics) }),
      /* @__PURE__ */ o.jsx(sn, { name: "arrow" })
    ] }, k.id)) : u.length === 0 ? /* @__PURE__ */ o.jsxs("div", { className: "empty-list", children: [
      "No runs yet — ",
      /* @__PURE__ */ o.jsx("button", { type: "button", className: "empty-link", onClick: y, children: "analyze a case" }),
      " to get started."
    ] }) : /* @__PURE__ */ o.jsx("div", { className: "empty-list", children: "No runs match these filters." }) })
  ] });
}
function $f({ disabled: u, onImport: a }) {
  const c = fe.useRef(null), [y, w] = fe.useState(""), x = async (T) => {
    if (T) {
      if (T.size > 10 * 1024 * 1024) {
        w("Portable bundles must be 10 MiB or smaller.");
        return;
      }
      w(""), a(await T.text(), T.name), c.current && (c.current.value = "");
    }
  };
  return /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsx("input", { ref: c, hidden: !0, type: "file", accept: "application/json,.json", onChange: (T) => {
      var L;
      return void x((L = T.target.files) == null ? void 0 : L[0]);
    } }),
    /* @__PURE__ */ o.jsxs("button", { type: "button", className: "secondary", disabled: u, onClick: () => {
      var T;
      return (T = c.current) == null ? void 0 : T.click();
    }, children: [
      /* @__PURE__ */ o.jsx(sn, { name: "upload" }),
      "Import JSON"
    ] }),
    y && /* @__PURE__ */ o.jsx("span", { className: "field-error", role: "alert", children: y })
  ] });
}
function ep({ payload: u, quickPrompt: a, setQuickPrompt: c, selectedId: y, setSelectedId: w, busy: x, motion: T, onAction: L, onPrepareRerun: z, onAnalyze: k }) {
  var le, ve, K, X;
  const H = u.runs ?? [], B = u.selectedRun ?? H.find((ie) => ie.id === y) ?? null, J = String(((le = u.setup) == null ? void 0 : le.task) ?? "faithfulness") === "faithfulness";
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content runs-workspace", children: [
    /* @__PURE__ */ o.jsxs("form", { className: "quick-run", onSubmit: (ie) => {
      ie.preventDefault(), a.trim() && !x && J && L("submit", { task: "faithfulness", mode: "quickPrompt", context: "", question: "", suppliedAnswer: "", prompt: a, exampleId: null });
    }, children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Quick run" }),
        /* @__PURE__ */ o.jsx("h2", { children: "Ask without building a thread." }),
        /* @__PURE__ */ o.jsx("p", { children: "Each prompt becomes an independent, auditable run." })
      ] }),
      /* @__PURE__ */ o.jsx(et, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 3, value: a, placeholder: "Ask the active generator…", onChange: (ie) => c(ie.target.value), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        /* @__PURE__ */ o.jsxs("button", { type: "submit", className: "primary", title: J ? void 0 : "Quick Run requires a faithfulness detector.", disabled: !a.trim() || x || !De((ve = u.capabilities) == null ? void 0 : ve.canGenerate) || !J, children: [
          /* @__PURE__ */ o.jsx(sn, { name: "spark" }),
          "Run prompt"
        ] }),
        /* @__PURE__ */ o.jsx($f, { disabled: !De((K = u.capabilities) == null ? void 0 : K.canImport), onImport: (ie) => L("import", { json: ie }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", disabled: !H.length || !De((X = u.capabilities) == null ? void 0 : X.canExport), onClick: () => L("exportBundle", {}), children: [
          /* @__PURE__ */ o.jsx(sn, { name: "download" }),
          "Export session"
        ] })
      ] })
    ] }),
    x && /* @__PURE__ */ o.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }),
    /* @__PURE__ */ o.jsxs("div", { className: "runs-grid", children: [
      /* @__PURE__ */ o.jsx(_f, { runs: H, selectedId: (B == null ? void 0 : B.id) ?? y, onSelect: (ie) => {
        w(ie.id), L("selectRun", { runId: ie.id });
      }, onAnalyze: k }),
      /* @__PURE__ */ o.jsx("aside", { className: "run-detail", children: B ? /* @__PURE__ */ o.jsx(Jo, { run: B, motion: T, onAction: L, onPrepareRerun: z }, B.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
        /* @__PURE__ */ o.jsx("h2", { children: "Select a run" }),
        /* @__PURE__ */ o.jsx("p", { children: "Its outcome, evidence, and provenance will appear here." })
      ] }) })
    ] })
  ] });
}
function np(u) {
  return u ? Array.isArray(u) ? u : Object.entries(u).map(([a, c]) => ({ label: kn(a), value: typeof c == "object" ? JSON.stringify(c) : c })) : [];
}
function tp({ diagnostics: u }) {
  var c;
  const a = u == null ? void 0 : u.attention;
  return (c = a == null ? void 0 : a.values) != null && c.length ? /* @__PURE__ */ o.jsxs("section", { className: "attention-card", children: [
    /* @__PURE__ */ o.jsx("div", { className: "section-heading", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Attention" }),
      /* @__PURE__ */ o.jsx("h2", { children: a.title ?? "Bounded attention summary" })
    ] }) }),
    /* @__PURE__ */ o.jsx("div", { className: "table-scroll", children: /* @__PURE__ */ o.jsxs("table", { children: [
      /* @__PURE__ */ o.jsx("thead", { children: /* @__PURE__ */ o.jsxs("tr", { children: [
        /* @__PURE__ */ o.jsx("th", { children: "Token" }),
        (a.columnLabels ?? []).map((y) => /* @__PURE__ */ o.jsx("th", { children: y }, y))
      ] }) }),
      /* @__PURE__ */ o.jsx("tbody", { children: a.values.map((y, w) => {
        var x;
        return /* @__PURE__ */ o.jsxs("tr", { children: [
          /* @__PURE__ */ o.jsx("th", { children: ((x = a.rowLabels) == null ? void 0 : x[w]) ?? w + 1 }),
          y.map((T, L) => /* @__PURE__ */ o.jsx("td", { style: T === null ? void 0 : { "--attention": String(Math.max(0, Math.min(1, T))) }, children: /* @__PURE__ */ o.jsx("span", { children: T === null ? "—" : T.toFixed(2) }) }, L))
        ] }, w);
      }) })
    ] }) }),
    a.note && /* @__PURE__ */ o.jsx("p", { className: "caption", children: a.note })
  ] }) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
    /* @__PURE__ */ o.jsx("h2", { children: "No attention summary yet" }),
    /* @__PURE__ */ o.jsx("p", { children: "Attention summaries appear here when the active detector captures them." })
  ] });
}
function rp({ payload: u, busy: a, onAction: c }) {
  var L;
  const y = u.diagnostics, w = u.capabilities ?? {}, x = y != null && y.metrics ? np(y.metrics) : [
    { label: "Runtime", value: (y == null ? void 0 : y.runtime) ?? "Python" },
    { label: "Device", value: (y == null ? void 0 : y.device) ?? "Loads on first run" },
    { label: "Model", value: (y == null ? void 0 : y.activeModel) ?? (y != null && y.modelLoaded ? "Loaded" : "Loads on first run") },
    { label: "Attention", value: y != null && y.attentionAvailable ? "Available" : "Not captured in this mode" }
  ], T = !!((L = u.capabilities) != null && L.trustedLocal);
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content diagnostics-workspace", children: [
    !T && /* @__PURE__ */ o.jsx("div", { className: "privacy-banner", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("b", { children: "Shared-safe diagnostics" }),
      /* @__PURE__ */ o.jsx("span", { children: "Sensitive paths, traces, provider responses, and raw runtime errors remain hidden." })
    ] }) }),
    a && /* @__PURE__ */ o.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }),
    T && (De(w.canRefreshDiagnostics, !1) || De(w.canOpenCachedAttention, !1) || De(w.canOpenLiveAttention, !1) || De(w.canUnloadModels, !1)) && /* @__PURE__ */ o.jsxs("div", { className: "diagnostic-actions", children: [
      De(w.canRefreshDiagnostics, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("refreshDiagnostics", {}), children: "Refresh runtime" }),
      De(w.canOpenCachedAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openCachedAttention", {}), children: "Cached attention explorer" }),
      De(w.canOpenLiveAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openLiveAttention", {}), children: "Live attention capture" }),
      De(w.canUnloadModels, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: a, onClick: () => c("unloadModels", {}), children: "Unload models" })
    ] }),
    /* @__PURE__ */ o.jsx("section", { className: "metric-grid", children: x.length ? x.map((z) => /* @__PURE__ */ o.jsxs("article", { className: Bl(z.status), children: [
      /* @__PURE__ */ o.jsx("span", { children: z.label }),
      /* @__PURE__ */ o.jsx("strong", { children: z.value === null ? "Not captured in this mode" : String(z.value) }),
      z.detail && /* @__PURE__ */ o.jsx("small", { children: z.detail })
    ] }, z.label)) : /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsx("span", { children: "Runtime status" }),
      /* @__PURE__ */ o.jsx("strong", { children: (y == null ? void 0 : y.status) ?? "Ready" }),
      /* @__PURE__ */ o.jsx("small", { children: "Refresh to request a safe server summary." })
    ] }) }),
    (y == null ? void 0 : y.message) && /* @__PURE__ */ o.jsx("div", { className: "inline-notice info", children: y.message }),
    /* @__PURE__ */ o.jsx(tp, { diagnostics: y }),
    T && (y == null ? void 0 : y.details) && /* @__PURE__ */ o.jsxs("details", { className: "diagnostic-details", children: [
      /* @__PURE__ */ o.jsx("summary", { children: "Trusted-local details" }),
      /* @__PURE__ */ o.jsx("dl", { children: Object.entries(y.details).map(([z, k]) => /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("dt", { children: kn(z) }),
        /* @__PURE__ */ o.jsx("dd", { children: typeof k == "object" ? JSON.stringify(k) : String(k) })
      ] }, z)) })
    ] })
  ] });
}
function lp(u) {
  try {
    const a = URL.createObjectURL(new Blob([u.content], { type: u.mimeType ?? "application/json" })), c = document.createElement("a");
    return c.href = a, c.download = u.fileName, c.click(), URL.revokeObjectURL(a), !0;
  } catch {
    return !1;
  }
}
function ip({ componentKey: u, payload: a, setStateValue: c, setTriggerValue: y }) {
  var Ve, V, b, Ce, Ue, Me, ae, O;
  const w = a.viewState, x = Ul.get(u) ?? { sequence: 0, draft: Df(a.draft), workspace: (w == null ? void 0 : w.workspace) ?? "analyze", appearance: (w == null ? void 0 : w.appearance) ?? Mf, selectedRunId: null, seenDownload: null, focusWorkspace: null };
  Ul.has(u) || Ul.set(u, x);
  const [T, L] = fe.useState(x.workspace), [z, k] = fe.useState(x.appearance), [H, B] = fe.useState(x.draft), [J, le] = fe.useState(x.selectedRunId), [ve, K] = fe.useState(!1), X = fe.useRef(null), ie = (Ve = a.actionReceipt) == null ? void 0 : Ve.sequence;
  fe.useEffect(() => K(!1), [ie, (V = a.activity) == null ? void 0 : V.status, a.runsRevision]), fe.useEffect(() => {
    w != null && w.workspace && w.workspace !== x.workspace && (x.workspace = w.workspace, L(w.workspace)), w != null && w.appearance && (w.appearance.theme !== x.appearance.theme || w.appearance.motion !== x.appearance.motion) && (x.appearance = w.appearance, k(w.appearance));
  }, [w == null ? void 0 : w.workspace, (b = w == null ? void 0 : w.appearance) == null ? void 0 : b.theme, (Ce = w == null ? void 0 : w.appearance) == null ? void 0 : Ce.motion, x]), fe.useEffect(() => {
    document.documentElement.dataset.sirinMotion = z.motion;
  }, [z.motion]), fe.useEffect(() => {
    var h;
    const P = x.focusWorkspace;
    if (!P || (w == null ? void 0 : w.workspace) !== P) return;
    const R = (h = X.current) == null ? void 0 : h.querySelector(`[data-workspace-tab="${P}"]`);
    R && (R.focus(), x.focusWorkspace = null);
  }, [w == null ? void 0 : w.workspace, x]), fe.useEffect(() => {
    if (!a.download) {
      x.seenDownload = null;
      return;
    }
    const P = a.download ? `${a.download.fileName}:${a.download.content.length}` : null;
    if (a.download && P !== x.seenDownload && (x.seenDownload = P, lp(a.download))) {
      x.sequence += 1;
      const R = { protocolVersion: a.protocolVersion, clientInstanceId: nc(), sequence: x.sequence, actionId: tc(), type: "clearDownload", expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: {} };
      y("action", R);
    }
  }, [a.download, a.protocolVersion, a.setupRevision, a.runsRevision, x, y]);
  const Ee = ve || ["queued", "running"].includes(((Ue = a.activity) == null ? void 0 : Ue.status) ?? ""), pe = (P) => {
    x.workspace = P, x.focusWorkspace = P, L(P), y("viewState", { workspace: P, appearance: x.appearance });
  }, ge = (P, R = !1) => {
    const h = { ...H, analyze: P };
    x.draft = h, B(h), R && c("draft", h);
  }, Pe = (P, R = !1) => {
    const h = { ...H, quickPrompt: P };
    x.draft = h, B(h), R && c("draft", h);
  }, we = (P) => {
    x.selectedRunId = P, le(P), c("selectedRunId", P);
  }, G = (P) => {
    var Z;
    const R = P.inputs ?? {}, S = { task: ((Z = P.setupSnapshot) == null ? void 0 : Z.task) ?? P.task ?? "faithfulness", mode: R.suppliedAnswer ? "supplied" : "generate", exampleId: null, context: R.context ?? "", question: R.question ?? "", answer: R.suppliedAnswer ?? "", prompt: R.prompt ?? "", sourceRunId: P.id };
    ge(S, !0), pe("analyze");
  }, oe = (P, R) => {
    if (Ee) return;
    x.sequence += 1;
    const h = { protocolVersion: a.protocolVersion, clientInstanceId: nc(), sequence: x.sequence, actionId: tc(), type: P, expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: R };
    K(!["selectRun"].includes(P)), y("action", h);
  }, Xe = (P, R) => {
    pe("compare"), oe("runCompare", { inputs: R, presetB: P });
  }, Fe = a.notices ?? [];
  return /* @__PURE__ */ o.jsx("div", { ref: X, className: "sirin-workspace", "data-theme": z.theme, "data-motion": z.motion, children: /* @__PURE__ */ o.jsxs("div", { className: "shell", children: [
    /* @__PURE__ */ o.jsx(Vf, { workspace: T, onWorkspace: pe, setup: a.setup, title: (Me = a.ui) == null ? void 0 : Me.title, subtitle: (ae = a.ui) == null ? void 0 : ae.subtitle }),
    Fe.length > 0 && /* @__PURE__ */ o.jsx("div", { className: "notice-stack", "aria-live": "polite", children: Fe.map((P, R) => /* @__PURE__ */ o.jsxs("div", { className: `inline-notice ${P.level ?? P.kind ?? "info"}`, children: [
      P.title && /* @__PURE__ */ o.jsx("b", { children: P.title }),
      /* @__PURE__ */ o.jsx("span", { children: P.message })
    ] }, R)) }),
    ((O = a.actionReceipt) == null ? void 0 : O.status) === "rejected" && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error receipt", role: "alert", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Action rejected" }),
      /* @__PURE__ */ o.jsx("span", { children: a.actionReceipt.message ?? "The request could not be accepted." })
    ] }),
    T === "analyze" && /* @__PURE__ */ o.jsx(Kf, { payload: a, draft: H.analyze, setDraft: ge, busy: Ee, motion: z.motion, onAction: oe, onPrepareRerun: G, onCompare: Xe }),
    T === "runs" && /* @__PURE__ */ o.jsx(ep, { payload: a, quickPrompt: H.quickPrompt, setQuickPrompt: Pe, selectedId: J, setSelectedId: we, busy: Ee, motion: z.motion, onAction: oe, onPrepareRerun: G, onAnalyze: () => pe("analyze") }),
    T === "compare" && /* @__PURE__ */ o.jsx(Yf, { payload: a, motion: z.motion, onAction: oe, onPrepareRerun: G, onBack: () => pe("analyze") }),
    T === "diagnostics" && /* @__PURE__ */ o.jsx(rp, { payload: a, busy: Ee, onAction: oe }),
    /* @__PURE__ */ o.jsxs("footer", { children: [
      /* @__PURE__ */ o.jsx("span", { children: "SIRIN" }),
      /* @__PURE__ */ o.jsx("span", { children: "Detector confidence is not automatically a calibrated probability." })
    ] })
  ] }) });
}
const Er = /* @__PURE__ */ new WeakMap(), zr = /* @__PURE__ */ new Map();
function op(u) {
  for (const [a, c] of zr)
    a !== u && !c.isConnected && (Ul.delete(a), zr.delete(a));
}
const sp = ({ data: u, key: a, parentElement: c, setStateValue: y, setTriggerValue: w }) => {
  Ff(), Of(c);
  let x = Er.get(c);
  if (x && (!x.container.isConnected || x.container.parentNode !== c)) {
    try {
      x.root.unmount();
    } catch {
    }
    x.container.remove(), Er.delete(c), x = void 0;
  }
  if (!x) {
    c.querySelectorAll(".sirin-component-root").forEach((z) => z.remove());
    const L = document.createElement("div");
    L.className = "sirin-component-root", c.append(L), x = { container: L, root: yf.createRoot(L) }, Er.set(c, x);
  }
  zr.set(a, x.container), op(a);
  const T = x;
  return T.root.render(/* @__PURE__ */ o.jsx(ip, { componentKey: a, payload: u, setStateValue: y, setTriggerValue: w })), () => {
    Er.get(c) === T && (Er.delete(c), zr.get(a) === T.container && zr.delete(a), T.root.unmount(), T.container.remove());
  };
};
export {
  sp as default
};
